# schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class FeedbackCreate(BaseModel):
    title: str
    content: str
    tag: str = "general"

class FeedbackOut(BaseModel):
    id: int
    title: str
    content: str
    tag: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # orm_mode는 v2에서는 이렇게 씀

class DataPointIn(BaseModel):
    user_id: int
    raw_json: dict

class DataPointOut(DataPointIn):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)



class ClusterJobCreate(BaseModel):
    datapoint_ids: list[UUID]
    n_clusters: int = 5


class ClusterJobOut(BaseModel):
    id: UUID
    status: str
    n_clusters: int
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class ClusterResult(BaseModel):
    label: int
    centroid: list[float]
    members: list[UUID]

# ─── User ───────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: UUID
    username: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ─── Post ───────────────────────────────────────────
class PostCreate(BaseModel):
    user_id: UUID
    title: str
    content: str
    password: str

# ─── Comment ────────────────────────────────────────
class _CommentBase(BaseModel):
    post_id: UUID
    user_id: str | None = None
    content: str
    parent_id: UUID | None = None      # 대댓글이면 부모 id

class CommentCreate(_CommentBase):
    password: str

class CommentOut(_CommentBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ─── 기타 ───────────────────────────────────────────
class ClusterRequest(BaseModel):
    n_clusters: int