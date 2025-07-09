from system.src.app.config.settings import settings
from system.src.app.usecases.generate_drafts_usecases.generate_drafts_usecase import GenerateDraftsUsecase
from system.src.app.usecases.query_docs_usecases.query_docs_usecase import QueryDocsUsecase
from fastapi import Depends

class GenerateDraftsController:
    def __init__(self,
        generate_drafts_usecase: GenerateDraftsUsecase = Depends(GenerateDraftsUsecase),
        query_docs_usecase: QueryDocsUsecase = Depends(QueryDocsUsecase),
    ):
        self.generate_drafts_usecase = generate_drafts_usecase
        self.query_docs_usecase = query_docs_usecase

    async def generate_drafts(self):
        query = "I've the doubt regarding the return of tokens, if you're available can you help me?"
        query = "integrations supported by the rocket?"
        response = await self.query_docs_usecase.query_docs(query, settings.ROCKET_DOCS_PINECONE_INDEX_NAME)
        return response
    