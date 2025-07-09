from fastapi import UploadFile

class DataInsertUsecase:
    def __init__(self):
        pass

    async def execute(self, file: UploadFile):
        return "Data inserted successfully"