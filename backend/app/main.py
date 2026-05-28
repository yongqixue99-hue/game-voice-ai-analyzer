from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .analyses import router as analyses_router
from .database import init_db, settings
from .recording_sessions import router as recording_sessions_router
from .recordings import router as recordings_router
from .segments import router as segments_router
from .session_summaries import router as session_summaries_router
from .transcriptions import router as transcriptions_router


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.audio_storage_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    yield


app = FastAPI(
    title="Game Voice AI Analyzer API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def health_payload() -> dict[str, str]:
    return {"status": "ok", "service": "fastapi", "version": app.version}


@app.get("/health", tags=["system"])
@app.get("/api/health", tags=["system"])
def health_check() -> dict[str, str]:
    return health_payload()


app.include_router(recordings_router)
app.include_router(recording_sessions_router)
app.include_router(session_summaries_router)
app.include_router(segments_router)
app.include_router(transcriptions_router)
app.include_router(analyses_router)
