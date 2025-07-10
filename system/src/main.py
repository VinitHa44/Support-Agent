from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from system.src.app.config.database import mongodb_database
from system.src.app.routes import (
    generate_drafts_route,
    insert_data_route,
    request_logs_route,
    websocket_route,
)


@asynccontextmanager
async def db_lifespan(app: FastAPI):
    mongodb_database.connect()

    yield

    mongodb_database.disconnect()


app = FastAPI(title="Rocket Classification System", lifespan=db_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    insert_data_route.router, prefix="/api/v1", tags=["Insert Data"]
)
app.include_router(
    generate_drafts_route.router, prefix="/api/v1", tags=["Generate Drafts"]
)
app.include_router(
    request_logs_route.router, prefix="/api/v1", tags=["Request Logs"]
)
app.include_router(websocket_route.router, prefix="/api/v1", tags=["WebSocket"])


@app.get("/")
async def root():
    return {"message": "Welcome to my FastAPI application!"}


if __name__ == "__main__":
    uvicorn.run(
        "system.src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["session-data/*", "intermediate_outputs/*"],
    )
