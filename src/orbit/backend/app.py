from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from orbit.database.session import init_db
from orbit.backend.api import router

app = FastAPI(title="ORBIT", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def on_startup():
    await init_db()
