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

        categorization_response = await self.categorization_usecase.execute(query)

        rocket_docs_query = categorization_response.get("doc_search_query")
        dataset_query = f"Subject: {categorization_response.get('subject')}\n{categorization_response.get('body')}"
        categories = categorization_response.get("categories")

        # Prepare search tasks, but only if the required data is present
        tasks = []
        
        # Check if rocket_docs_query is present and not empty
        if rocket_docs_query and rocket_docs_query.strip():
            rocket_docs_task = self.query_docs_usecase.query_docs(
                rocket_docs_query, settings.ROCKET_DOCS_PINECONE_INDEX_NAME
            )
            tasks.append(("rocket_docs", rocket_docs_task))
        else:
            print("Skipping rocket docs search - empty or missing doc_search_query")
            
        # Check if categories are present and not empty
        if categories and len(categories) > 0:
            dataset_task = self.query_docs_usecase.query_docs(
                dataset_query, settings.PINECONE_INDEX_NAME, categories=categories
            )
            tasks.append(("dataset", dataset_task))
        else:
            print("Skipping dataset search - empty or missing categories")

        # Execute available tasks
        results = {}
        if tasks:
            # Execute only the available tasks
            task_names = [task[0] for task in tasks]
            task_coroutines = [task[1] for task in tasks]
            task_results = await asyncio.gather(*task_coroutines)
            
            # Map results back to their names
            for name, result in zip(task_names, task_results):
                results[name] = result
        
        # Get results or empty lists if tasks were skipped
        rocket_docs_response = results.get("rocket_docs", [])
        dataset_response = results.get("dataset", [])

        generate_drafts_query = {
            "from": categorization_response.get("from"),
            "subject": categorization_response.get("subject"),
            "body": categorization_response.get("body"),
            "rocket_docs_response": rocket_docs_response,
            "dataset_response": dataset_response,
            "categories": categories if categories else [],  # Ensure categories is always a list
            "attachments": query.get("attachments", []),  # Pass attachments from original query
        }
        generate_drafts_response = (
            await self.generate_drafts_usecase.generate_drafts(
                generate_drafts_query
            )
        )

        # Return the generate_drafts_response instead of search results
        return generate_drafts_response
