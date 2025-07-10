from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from fastapi import HTTPException

from system.src.app.config.database import mongodb_database


class RequestLogRepository:
    def __init__(self):
        self.collection = mongodb_database.get_request_logs_collection()

    async def add_request_log(self, request_log_data: Dict) -> str:
        """
        Add a new request log to the database

        :param request_log_data: Request log data dictionary
        :return: ID of the created request log
        """
        try:
            # Add timestamp if not present
            if "timestamp" not in request_log_data:
                request_log_data["timestamp"] = datetime.now()

            result = await self.collection.insert_one(request_log_data)
            return str(result.inserted_id)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error adding request log: {str(e)}"
            )

    async def get_request_log_by_id(self, log_id: str) -> Optional[Dict]:
        """
        Get a request log by its ID

        :param log_id: The request log ID
        :return: Request log data or None if not found
        """
        try:
            result = await self.collection.find_one({"_id": ObjectId(log_id)})
            if result:
                # Add default values for new fields that might be missing in existing documents
                if "rocket_docs_count" not in result:
                    result["rocket_docs_count"] = 0
                if "dataset_docs_count" not in result:
                    result["dataset_docs_count"] = 0
                if "total_docs_retrieved" not in result:
                    result["total_docs_retrieved"] = 0
                if "rocket_docs_results" not in result:
                    result["rocket_docs_results"] = []
                if "dataset_results" not in result:
                    result["dataset_results"] = []

                # Ensure other fields have defaults
                if "categorization_categories" not in result:
                    result["categorization_categories"] = []
                if "new_categories_created" not in result:
                    result["new_categories_created"] = []
                if "doc_search_query" not in result:
                    result["doc_search_query"] = None
                if "multiple_drafts_generated" not in result:
                    result["multiple_drafts_generated"] = False
                if "user_reviewed" not in result:
                    result["user_reviewed"] = False
                if "has_new_categories" not in result:
                    result["has_new_categories"] = False
                if "has_attachments" not in result:
                    result["has_attachments"] = False
                if "required_docs" not in result:
                    result["required_docs"] = False

                result["id"] = str(result["_id"])
                del result["_id"]
            return result
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error fetching request log: {str(e)}"
            )

    async def get_request_logs_by_user(
        self, user_id: str, limit: int = 100
    ) -> List[Dict]:
        """
        Get request logs for a specific user

        :param user_id: User ID
        :param limit: Maximum number of logs to return
        :return: List of request logs
        """
        try:
            cursor = (
                self.collection.find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            logs = []
            async for log in cursor:
                # Add default values for new fields that might be missing in existing documents
                if "rocket_docs_count" not in log:
                    log["rocket_docs_count"] = 0
                if "dataset_docs_count" not in log:
                    log["dataset_docs_count"] = 0
                if "total_docs_retrieved" not in log:
                    log["total_docs_retrieved"] = 0
                if "rocket_docs_results" not in log:
                    log["rocket_docs_results"] = []
                if "dataset_results" not in log:
                    log["dataset_results"] = []

                # Ensure other fields have defaults
                if "categorization_categories" not in log:
                    log["categorization_categories"] = []
                if "new_categories_created" not in log:
                    log["new_categories_created"] = []
                if "doc_search_query" not in log:
                    log["doc_search_query"] = None
                if "multiple_drafts_generated" not in log:
                    log["multiple_drafts_generated"] = False
                if "user_reviewed" not in log:
                    log["user_reviewed"] = False
                if "has_new_categories" not in log:
                    log["has_new_categories"] = False
                if "has_attachments" not in log:
                    log["has_attachments"] = False
                if "required_docs" not in log:
                    log["required_docs"] = False

                log["id"] = str(log["_id"])
                del log["_id"]
                logs.append(log)
            return logs
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching user request logs: {str(e)}",
            )

    async def get_request_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Get request statistics for analytics

        :param start_date: Start date for statistics
        :param end_date: End date for statistics
        :return: Statistics dictionary
        """
        try:
            # Build match criteria
            match_criteria = {}
            if start_date or end_date:
                match_criteria["timestamp"] = {}
                if start_date:
                    match_criteria["timestamp"]["$gte"] = start_date
                if end_date:
                    match_criteria["timestamp"]["$lte"] = end_date

            # Aggregation pipeline for statistics
            pipeline = [
                (
                    {"$match": match_criteria}
                    if match_criteria
                    else {"$match": {}}
                ),
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "average_processing_time": {"$avg": "$processing_time"},
                        "requests_with_attachments": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$has_attachments", True]},
                                    1,
                                    0,
                                ]
                            }
                        },
                        "requests_requiring_docs": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$required_docs", True]},
                                    1,
                                    0,
                                ]
                            }
                        },
                        "requests_with_new_categories": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$has_new_categories", True]},
                                    1,
                                    0,
                                ]
                            }
                        },
                        "user_reviewed_requests": {
                            "$sum": {
                                "$cond": [
                                    {"$eq": ["$user_reviewed", True]},
                                    1,
                                    0,
                                ]
                            }
                        },
                        "all_categories": {"$push": "$categories"},
                        # Pinecone analytics with null handling
                        "total_docs_retrieved": {
                            "$sum": {"$ifNull": ["$total_docs_retrieved", 0]}
                        },
                        "rocket_docs_total": {
                            "$sum": {"$ifNull": ["$rocket_docs_count", 0]}
                        },
                        "dataset_docs_total": {
                            "$sum": {"$ifNull": ["$dataset_docs_count", 0]}
                        },
                        "requests_with_docs": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$gt": [
                                            {
                                                "$ifNull": [
                                                    "$total_docs_retrieved",
                                                    0,
                                                ]
                                            },
                                            0,
                                        ]
                                    },
                                    1,
                                    0,
                                ]
                            }
                        },
                    }
                },
            ]

            result = await self.collection.aggregate(pipeline).to_list(1)

            if not result:
                return {
                    "total_requests": 0,
                    "average_processing_time": 0.0,
                    "requests_with_attachments": 0,
                    "requests_requiring_docs": 0,
                    "new_categories_created_count": 0,
                    "user_review_rate": 0.0,
                    "most_common_categories": [],
                }

            stats = result[0]
            total_requests = stats["total_requests"]

            # Calculate user review rate
            user_review_rate = (
                (stats["user_reviewed_requests"] / total_requests * 100)
                if total_requests > 0
                else 0.0
            )

            # Flatten and count categories
            all_categories = []
            for cat_list in stats["all_categories"]:
                all_categories.extend(cat_list)

            # Count category frequencies
            category_counts = {}
            for category in all_categories:
                category_counts[category] = category_counts.get(category, 0) + 1

            # Get most common categories
            most_common_categories = [
                {"category": cat, "count": count}
                for cat, count in sorted(
                    category_counts.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            # Calculate Pinecone-related statistics
            average_docs_retrieved = (
                (stats["total_docs_retrieved"] / total_requests)
                if total_requests > 0
                else 0.0
            )
            docs_utilization_rate = (
                (stats["requests_with_docs"] / total_requests * 100)
                if total_requests > 0
                else 0.0
            )

            # Most retrieved doc types
            most_retrieved_doc_types = [
                {"type": "rocket_docs", "count": stats["rocket_docs_total"]},
                {"type": "dataset_docs", "count": stats["dataset_docs_total"]},
            ]

            return {
                "total_requests": total_requests,
                "average_processing_time": round(
                    stats["average_processing_time"] or 0.0, 2
                ),
                "requests_with_attachments": stats["requests_with_attachments"],
                "requests_requiring_docs": stats["requests_requiring_docs"],
                "new_categories_created_count": stats[
                    "requests_with_new_categories"
                ],
                "user_review_rate": round(user_review_rate, 2),
                "most_common_categories": most_common_categories,
                # Enhanced Pinecone statistics
                "average_docs_retrieved": round(average_docs_retrieved, 2),
                "most_retrieved_doc_types": most_retrieved_doc_types,
                "docs_utilization_rate": round(docs_utilization_rate, 2),
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching request statistics: {str(e)}",
            )
