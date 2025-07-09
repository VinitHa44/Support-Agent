from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from system.src.app.config.database import mongodb_database

# @asynccontextmanager
# async def db_lifespan(app: FastAPI):
#     mongodb_database.connect()

#     yield

#     mongodb_database.disconnect()


app = FastAPI(title="Rocket Classification System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to my FastAPI application!"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
