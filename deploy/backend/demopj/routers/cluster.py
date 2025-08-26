# routers/cluster.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from demopj.database import get_session
from demopj.models import DataPoint, ClusterJob, Cluster, ClusterMember
from demopj.schemas import ClusterRequest, ClusterJobOut, ClusterResult
from sklearn.cluster import KMeans            # pip install scikit-learn
import numpy as np
from uuid import UUID
import datetime
import select
from demopj.database import SYNC_DATABASE_URL  # ← 새 상수 import


router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.get("/job/{job_id}", response_model=ClusterJobOut)
async def get_job(job_id: UUID, db: AsyncSession = Depends(get_session)):
    job = await db.get(ClusterJob, job_id)
    if not job: raise HTTPException(404)
    return job

@router.get("/result/{job_id}", response_model=list[ClusterResult])
async def get_result(job_id: UUID, db: AsyncSession = Depends(get_session)):
    job = await db.get(ClusterJob, job_id)
    if not job or job.status != "done":
        raise HTTPException(404, "Job not finished or missing")
    res = await db.execute(
        select(Cluster).where(Cluster.job_id == job_id).order_by(Cluster.label)
    )
    clusters = res.scalars().all()
    output = []
    for c in clusters:
        mem_ids = [m.datapoint_id for m in c.members]
        output.append(
            ClusterResult(label=c.label,
                          centroid=c.centroid,
                          members=mem_ids)
        )
    return output


@router.post("/cluster", response_model=ClusterJobOut, status_code=202)
@router.post("/cluster", response_model=ClusterJobOut, status_code=202)
async def create_cluster_job(
    payload: ClusterRequest,  # 필요시 schema에서 datapoint_ids 필드 삭제
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    job = ClusterJob(n_clusters=payload.n_clusters, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # 이제는 게시글, 댓글에서 자동으로 데이터를 가져와 분석
    background_tasks.add_task(
        run_clustering, job.id, SYNC_DATABASE_URL
    )
    return job
  

async def run_clustering(job_id: UUID, db_url: str):
    from sqlalchemy import select, create_engine
    from sqlalchemy.orm import Session
    from sklearn.cluster import KMeans
    from demopj.models import Post
    import datetime
    import numpy as np

    engine = create_engine(db_url, future=True)

    with Session(engine) as s:
        job = s.get(ClusterJob, job_id)
        job.status, job.started_at = "running", datetime.datetime.utcnow()
        s.commit()

        # 📌 1. 게시글과 댓글 가져오기
        posts = s.execute(select(Post)).scalars().all()
        if not posts:
            job.status = "failed"
            s.commit()
            return

        raw_texts = [
            f"{post.title} {post.content} {' '.join(c.content for c in post.comments)}"
            for post in posts
        ]

        # 📌 2. 텍스트 → 벡터 변환 (임베딩)
        vectors = [simple_text_embedding(text) for text in raw_texts]

        # 📌 3. K-Means 수행
        km = KMeans(n_clusters=job.n_clusters, random_state=0)
        km.fit(vectors)

        # 📌 4. 클러스터링 결과 저장
        for lbl in range(job.n_clusters):
            cl = Cluster(
                job_id=job.id,
                label=lbl,
                centroid=km.cluster_centers_[lbl].tolist()
            )
            s.add(cl)
            s.flush()  # id 확보

            for post, vec, dist in zip(posts, vectors, km.transform(vectors)[:, lbl]):
                if km.labels_[posts.index(post)] == lbl:
                    s.add(ClusterMember(
                        cluster_id=cl.id,
                        datapoint_id=post.id,  # 여기선 post_id를 저장 (datapoint_id를 재활용)
                        distance=float(dist)
                    ))

        job.status = "done"
        job.finished_at = datetime.datetime.utcnow()
        s.commit()

def simple_text_embedding(text: str) -> list[float]:
    """
    초간단 텍스트 임베딩 함수 (예시용).
    실제 프로젝트에서는 Sentence-BERT나 OpenAI 임베딩 등 강력한 임베딩을 쓰세요.
    """
    return [len(text), sum(ord(c) for c in text) % 1000]


def flatten(raw: dict) -> list[float]:
    """👶🏻 예시 변환기: 숫자만 뽑아 정렬. 필요 시 여기 맞춤 수정."""
    return [v for _, v in sorted(raw.items()) if isinstance(v, (int, float))]
