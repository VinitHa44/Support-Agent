from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RequestLogCreateSchema(BaseModel):
    """Schema for creating a new request log"""
    
    request_id: str
    from_email: str
    subject: str
    body: str
    categories: List[str] = []
    has_new_categories: bool = False
    has_attachments: bool = False
    required_docs: bool = False
    draft_response: str
    processing_time: float = 0.0
    user_id: str = "default_user"
    categorization_categories: List[str] = []
    new_categories_created: List[str] = []
    doc_search_query: Optional[str] = None
    multiple_drafts_generated: bool = False
    user_reviewed: bool = False
    
    # Pinecone results fields
    rocket_docs_count: int = 0
    dataset_docs_count: int = 0
    rocket_docs_results: List[dict] = []
    dataset_results: List[dict] = []
    total_docs_retrieved: int = 0


class RequestLogResponseSchema(BaseModel):
    """Schema for request log response"""
    
    id: str
    request_id: str
    from_email: str
    subject: str
    body: str
    categories: List[str]
    has_new_categories: bool
    has_attachments: bool
    required_docs: bool
    draft_response: str
    processing_time: float
    timestamp: datetime
    user_id: str
    categorization_categories: List[str]
    new_categories_created: List[str]
    doc_search_query: Optional[str]
    multiple_drafts_generated: bool
    user_reviewed: bool
    
    # Pinecone results fields
    rocket_docs_count: int
    dataset_docs_count: int
    rocket_docs_results: List[dict]
    dataset_results: List[dict]
    total_docs_retrieved: int


class RequestLogStatsSchema(BaseModel):
    """Schema for request log statistics"""
    
    total_requests: int
    average_processing_time: float
    most_common_categories: List[dict]
    requests_with_attachments: int
    requests_requiring_docs: int
    new_categories_created_count: int
    user_review_rate: float
    
    # Enhanced statistics with Pinecone data
    average_docs_retrieved: float
    most_retrieved_doc_types: List[dict]
    docs_utilization_rate: float 