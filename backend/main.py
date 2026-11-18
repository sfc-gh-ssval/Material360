from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import upload, results, files, agent
from backend.services.snowflake import init_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_session()
    yield

app = FastAPI(
    title="Engineering Drawing Extraction API",
    description="Extract, search, and analyze engineering drawings using Snowflake Cortex AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(results.router)
app.include_router(files.router)
app.include_router(agent.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "drawing-extraction-api"}
