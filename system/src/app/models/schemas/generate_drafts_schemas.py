from typing import List, Optional

from pydantic import BaseModel


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

    subject: str
    sender: str
    body: str
    attachments: List[AttachmentSchema]