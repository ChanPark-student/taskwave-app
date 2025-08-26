# models.py
from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from demopj.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    tag: Mapped[str] = mapped_column(String(30), default="general")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

# models.py (추가 부분)
from sqlalchemy import Integer, Float, JSON, ForeignKey, UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
import uuid

class DataPoint(Base):
    __tablename__ = "data_points"

    id: Mapped[uuid.UUID] = mapped_column(
        default=uuid.uuid4, primary_key=True
    )
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    raw_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


from uuid import uuid4

class ClusterJob(Base):
    __tablename__ = "cluster_jobs"

    id = mapped_column(UUID, primary_key=True, default=uuid4)
    status = mapped_column(String(20), default="pending")
    n_clusters = mapped_column(Integer, default=5)

    # ✅ 두 칼럼을 nullable=True 로!
    started_at = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at = mapped_column(DateTime(timezone=True), nullable=True)

    clusters = relationship("Cluster", back_populates="job")

class Cluster(Base):               # 각 군집의 대표 정보
    __tablename__ = "clusters"
    id = mapped_column(Integer, primary_key=True)
    job_id = mapped_column(ForeignKey("cluster_jobs.id", ondelete="CASCADE"))
    label = mapped_column(Integer, index=True)
    centroid = mapped_column(JSON)               # [x, y, …]
    job = relationship("ClusterJob", back_populates="clusters")
    members = relationship("ClusterMember", back_populates="cluster")

class ClusterMember(Base):         # “데이터-군집 연결 표”
    __tablename__ = "cluster_members"
    cluster_id = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), primary_key=True)
    datapoint_id = mapped_column(ForeignKey("data_points.id", ondelete="CASCADE"), primary_key=True)
    distance = mapped_column(Float)
    cluster = relationship("Cluster", back_populates="members")


class User(Base):
    __tablename__ = "users"

    id            = mapped_column(UUID, primary_key=True, default=uuid4)
    username      = mapped_column(String(50), unique=True, nullable=False)
    password_hash = mapped_column(String(128), nullable=False)
    created_at    = mapped_column(DateTime(timezone=True),
                                  server_default=func.now())

# ──────────────────────────────────────────────────────────────
class Post(Base):
    __tablename__ = "posts"

    id         = mapped_column(UUID, primary_key=True, default=uuid4)
    user_id    = mapped_column(ForeignKey("users.id"))
    title      = mapped_column(String(200), nullable=False)
    content    = mapped_column(Text, nullable=False)
    password   = mapped_column(String(128), nullable=False)
    created_at = mapped_column(DateTime(timezone=True),
                               server_default=func.now())

    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan"
    )

# ──────────────────────────────────────────────────────────────
class Comment(Base):
    __tablename__ = "comments"

    id         = mapped_column(UUID, primary_key=True, default=uuid4)
    post_id    = mapped_column(ForeignKey("posts.id"), nullable=False)
    parent_id  = mapped_column(ForeignKey("comments.id"), nullable=True)
    user_id    = mapped_column(String(50), nullable=True)
    content    = mapped_column(Text, nullable=False)
    password   = mapped_column(String(128), nullable=False)
    created_at = mapped_column(DateTime(timezone=True),
                               server_default=func.now())

    # ── 관계 ────────────────────────────────────────────
    post = relationship("Post", back_populates="comments")

    parent = relationship(
        "Comment",
        remote_side=lambda: [Comment.id],
        backref=backref("children", cascade="all, delete-orphan")
    )