from fastapi import FastAPI
from routers import battle, offline

app = FastAPI()

app.include_router(battle.router)
app.include_router(offline.router)