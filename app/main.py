from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(router, prefix='/api')

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / 'frontend'
if FRONTEND.exists():
    app.mount('/static', StaticFiles(directory=str(FRONTEND)), name='static')


@app.get('/')
def index():
    index_file = FRONTEND / 'index.html'
    if index_file.exists():
        return FileResponse(index_file)
    return {'message': settings.app_name, 'docs': '/docs'}
