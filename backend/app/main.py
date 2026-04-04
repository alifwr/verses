from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, SessionLocal, Base
from app.middleware import AdabCurfewMiddleware
from app.seed import seed_users
from app.routes.auth import router as auth_router
from app.routes.rules import router as rules_router
from app.routes.questions import router as questions_router
from app.routes.milestones import router as milestones_router
from app.routes.activity import router as activity_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://100.126.226.100:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AdabCurfewMiddleware)


app.include_router(auth_router)
app.include_router(rules_router)
app.include_router(questions_router)
app.include_router(milestones_router)
app.include_router(activity_router)


@app.get("/health")
def health():
    return {"status": "ok"}
