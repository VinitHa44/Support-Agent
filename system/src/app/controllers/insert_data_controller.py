from system.src.app.usecases.data_insert_usecases.data_insert_usecase import DataInsertUsecase
from fastapi import Depends, UploadFile

class InsertDataController:
    def __init__(self,
        data_insert_usecase: DataInsertUsecase = Depends(DataInsertUsecase),
    ):
        self.data_insert_usecase = data_insert_usecase

    async def insert_data(self, file: UploadFile):
        return await self.data_insert_usecase.execute(file)