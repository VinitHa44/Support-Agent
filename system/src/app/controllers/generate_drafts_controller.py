import asyncio
from typing import Dict

from fastapi import Depends

from system.src.app.config.settings import settings
from system.src.app.usecases.categorisation_usecase.categorisation_usecase import (
    CategorizationUsecase,
)
from system.src.app.usecases.generate_drafts_usecases.generate_drafts_usecase import (
    GenerateDraftsUsecase,
)
from system.src.app.usecases.query_docs_usecases.query_docs_usecase import (
    QueryDocsUsecase,
)


class GenerateDraftsController:
    def __init__(
        self,
        generate_drafts_usecase: GenerateDraftsUsecase = Depends(
            GenerateDraftsUsecase
        ),
        query_docs_usecase: QueryDocsUsecase = Depends(QueryDocsUsecase),
        categorization_usecase: CategorizationUsecase = Depends(
            CategorizationUsecase
        ),
    ):
        self.generate_drafts_usecase = generate_drafts_usecase
        self.query_docs_usecase = query_docs_usecase
        self.categorization_usecase = categorization_usecase

    async def generate_drafts(self, query: Dict):

        categorization_response = self.categorization_usecase.execute(query)

        rocket_docs_query = categorization_response.get("doc_search_query")
        dataset_query = f"Subject: {categorization_response.get('subject')}\n{categorization_response.get('body')}"
        categories = categorization_response.get("categories")

        rocket_docs_task = self.query_docs_usecase.query_docs(
            rocket_docs_query, settings.ROCKET_DOCS_PINECONE_INDEX_NAME
        )

        dataset_task = self.query_docs_usecase.query_docs(
            dataset_query, settings.PINECONE_INDEX_NAME, categories=categories
        )

        rocket_docs_response, dataset_response = await asyncio.gather(
            rocket_docs_task, dataset_task
        )

        response = {
            "rocket_docs_response": rocket_docs_response,
            "dataset_response": dataset_response,
        }
        return response
