from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import config
from routes.auth import auth_router
from routes.user import user_router
from db.db_setup import init_db
import uvicorn


app = FastAPI(debug=config.DEBUG, title='T')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(auth_router, prefix='/auth', tags=['auth'])
app.include_router(user_router, prefix='/user', tags=['auth'])


@app.on_event('startup')
async def on_startup():
    await init_db()

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
