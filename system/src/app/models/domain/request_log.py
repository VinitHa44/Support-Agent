from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RequestLog(BaseModel):
    """Domain model for request logging"""

    request_id: str = Field(
        ..., description="Unique identifier for the request"
    )
    from_email: str = Field(..., description="User's email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="User's original query/email body")
    categories: List[str] = Field(
        default=[], description="Combined categories + new_categories"
    )
    has_new_categories: bool = Field(
        default=False,
        description="Flag indicating if new categories were created",
    )
    has_attachments: bool = Field(
        default=False, description="Flag indicating if request had attachments"
    )
    required_docs: bool = Field(
        default=False,
        description="Flag indicating if documentation search was required",
    )
    draft_response: str = Field(..., description="Final draft sent as response")
    processing_time: float = Field(
        default=0.0, description="Time taken to process the request in seconds"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the request was processed",
    )
    user_id: str = Field(
        default="default_user", description="User ID for the request"
    )

    # Additional metadata for statistics
    categorization_categories: List[str] = Field(
        default=[], description="Original categories from categorization"
    )
    new_categories_created: List[str] = Field(
        default=[], description="New categories that were created"
    )
    doc_search_query: Optional[str] = Field(
        None, description="Query used for document search"
    )
    multiple_drafts_generated: bool = Field(
        default=False, description="Whether multiple drafts were generated"
    )
    user_reviewed: bool = Field(
        default=False, description="Whether user reviewed multiple drafts"
    )

    # Pinecone results metadata
    rocket_docs_count: int = Field(
        default=0, description="Number of rocket docs retrieved from Pinecone"
    )
    dataset_docs_count: int = Field(
        default=0, description="Number of dataset docs retrieved from Pinecone"
    )
    rocket_docs_results: List[Dict] = Field(
        default=[], description="Top rocket docs results with metadata"
    )
    dataset_results: List[Dict] = Field(
        default=[], description="Top dataset results with metadata"
    )
    total_docs_retrieved: int = Field(
        default=0,
        description="Total number of documents retrieved from Pinecone",
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
