from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ImageTags(BaseModel):
    subject: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=40)
    attributes: list[str] = Field(min_length=1, max_length=8)
    caption: str = Field(min_length=8, max_length=400)
    confidence: float = Field(ge=0, le=1)


class PostCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]{3,80}$")
    title: str = Field(min_length=3, max_length=180)
    body: str = Field(min_length=10, max_length=5000)
    subject: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=40)


class ReviewCreate(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = Field(default="", max_length=1000)


class JobResponse(BaseModel):
    id: UUID
    status: str
    attempts: int
    processed: int
    total: int

