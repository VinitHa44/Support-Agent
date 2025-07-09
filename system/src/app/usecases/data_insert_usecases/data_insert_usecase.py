from fastapi import Depends, UploadFile
import json
import os
from system.src.app.config.settings import settings
from system.src.app.usecases.query_docs_usecases.query_docs_usecase import QueryDocsUsecase
from system.src.app.usecases.data_insert_usecases.data_insert_usecase_helper import DataInsertUsecaseHelper

class DataInsertUsecase:
    def __init__(self,
        data_insert_usecase_helper: DataInsertUsecaseHelper = Depends(DataInsertUsecaseHelper),
        query_docs_usecase: QueryDocsUsecase = Depends(QueryDocsUsecase)
    ):
        self.data_insert_usecase_helper = data_insert_usecase_helper
        self.query_docs_usecase = query_docs_usecase

    async def _process_file(self, file: UploadFile):
        try:
            content = await file.read()
            data = json.loads(content.decode('utf-8'))
            categories = {"categories": data.get('categories', [])}
            examples = data.get('examples', [])
            
            # Ensure the directory exists
            os.makedirs('session-data', exist_ok=True)
            with open('session-data/categories.json', 'w') as f:
                json.dump(categories, f)
            return examples
                
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format"}
        except Exception as e:
            return {"error": f"Error processing file: {str(e)}"}

    async def execute(self, file: UploadFile):
        try:
            examples = await self._process_file(file)
            embeddings = await self.data_insert_usecase_helper.generate_embeddings(examples)
            upsert_result = await self.data_insert_usecase_helper.upsert_chunks_in_pinecone(embeddings)

            # query_rocket_docs = "What is the C.L.E.A.R. framework?"
            # query_dataset = "I've the doubt regarding the return of tokens, if you're available can you help me?"
            # query_dataset = "capital of france?"
            # response = await self.query_docs_usecase.query_docs(query_dataset, settings.PINECONE_INDEX_NAME)
            # response_rocket_docs = await self.query_docs_usecase.query_docs(query_rocket_docs, settings.ROCKET_DOCS_PINECONE_INDEX_NAME)
            return {
                "examples_processed": len(examples),
                "embeddings_generated": len(embeddings),
                "upserted_count": upsert_result.get("upserted_count", 0),
                # "query_response": response,
                # "query_rocket_docs_response": response_rocket_docs,
                "status": "success"
            }
        except Exception as e:
            return {"error": f"Error processing execute function in data_insert_usecase: {str(e)}"}