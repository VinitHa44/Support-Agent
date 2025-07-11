from typing import Dict

from fastapi import Depends

from system.src.app.repositories.error_repository import ErrorRepo
from system.src.app.usecases.data_insert_usecases.data_insert_usecase import (
    DataInsertUsecase,
)


class TemplateStorageUsecase:
    def __init__(
        self,
        data_insert_usecase: DataInsertUsecase = Depends(DataInsertUsecase),
        error_repo: ErrorRepo = Depends(ErrorRepo),
    ):
        self.data_insert_usecase = data_insert_usecase
        self.error_repo = error_repo

    async def store_response_template(
        self, categorization_response: Dict, final_draft: str
    ):
        """
        Store the final response as a template for future reference

        :param categorization_response: Categorization results containing categories and email data
        :param final_draft: The final draft response to store
        :return: Result from data insert usecase
        """
        try:
            # Combine categories and new_categories
            categories = categorization_response.get("categories", [])
            new_categories = categorization_response.get("new_categories", [])
            combined_categories = categories + new_categories

            # Create the template in the required format
            template_data = [
                {
                    "subject": categorization_response.get("subject", ""),
                    "from": categorization_response.get("from", ""),
                    "query": categorization_response.get("body", ""),
                    "response": final_draft,
                    "categories": combined_categories,
                }
            ]

            # Call data insert usecase to store the template
            result = await self.data_insert_usecase.execute(
                new_template=template_data
            )
            print(f"Successfully stored response template: {result}")
            return result

        except Exception as e:
            error_msg = f"Failed to store response template: {str(e)}"
            await self.error_repo.log_error(
                error=error_msg,
                additional_context={
                    "file": "template_storage_usecase.py",
                    "method": "store_response_template",
                    "operation": "template_storage",
                    "response_text": error_msg,
                    "subject": categorization_response.get("subject", ""),
                    "categories": categorization_response.get("categories", []),
                    "new_categories": categorization_response.get("new_categories", []),
                    "template_size": len(template_data) if 'template_data' in locals() else 0,
                },
            )
            # Log the error but don't fail the main process
            print(f"Warning: Failed to store response template: {error_msg}")
            raise e
