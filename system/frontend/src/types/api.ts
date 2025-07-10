export interface RequestLogStats {
  total_requests: number;
  average_processing_time: number;
  most_common_categories: Array<{ category: string; count: number }>;
  requests_with_attachments: number;
  requests_requiring_docs: number;
  new_categories_created_count: number;
  user_review_rate: number;
  
  // Enhanced Pinecone statistics
  average_docs_retrieved: number;
  most_retrieved_doc_types: Array<{ type: string; count: number }>;
  docs_utilization_rate: number;
}

export interface RequestLog {
  id: string;
  request_id: string;
  from_email: string;
  subject: string;
  body: string;
  categories: string[];
  has_new_categories: boolean;
  has_attachments: boolean;
  required_docs: boolean;
  draft_response: string;
  processing_time: number;
  timestamp: string;
  user_id: string;
  categorization_categories: string[];
  new_categories_created: string[];
  doc_search_query?: string;
  multiple_drafts_generated: boolean;
  user_reviewed: boolean;
  
  // Pinecone results fields
  rocket_docs_count: number;
  dataset_docs_count: number;
  rocket_docs_results: Array<{ score: number; id: string; metadata: any }>;
  dataset_results: Array<{ score: number; id: string; metadata: any }>;
  total_docs_retrieved: number;
}

export interface DraftData {
  from: string;
  body: string;
  subject: string;
  drafts: string[];
} 