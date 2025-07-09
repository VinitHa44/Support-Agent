from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AttachmentSchema(BaseModel):
    """Schema for email attachments"""
    filename: str
    mime_type: str
    size: int
    attachment_id: str
    is_image: bool
    is_inline: bool
    base64_data: Optional[str] = None
    data_uri: Optional[str] = None


class GenerateDraftsRequestSchema(BaseModel):
    """Schema for generate drafts request"""
    id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    message_id: str
    in_reply_to: Optional[str] = None
    body: str
    attachments: List[AttachmentSchema]
    has_images: bool
    is_unread: bool
    internal_date: str
    labels: List[str]