from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from config import settings
from db import Base, apply_sqlite_migrations, engine
from models import User
from routers.audio import router as audio_router
from routers.excel import router as excel_router
from routers.check import router as check_router
from routers.gps import router as gps_router
from routers.admin import router as admin_router
from routers.auth import router as auth_router
from services.security import hash_password


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(audio_router)
app.include_router(excel_router)
app.include_router(check_router)
app.include_router(gps_router)

app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


static_path = Path(settings.static_dir)
if static_path.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(static_path)),
        name="static",
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index():
    index_file = static_path / "index.html"
    if index_file.exists():
        content = index_file.read_text(encoding="utf-8")
        return HTMLResponse(
            content=content,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
    return HTMLResponse("<h1>index.html not found in static/</h1>", status_code=404)


@app.get("/lame.min.js", include_in_schema=False)
async def lame_js():
    lame_file = static_path / "lame.min.js"
    if lame_file.exists():
        return FileResponse(
            str(lame_file),
            media_type="application/javascript",
            headers={"Cache-Control": "public, max-age=604800"},
        )
    return HTMLResponse("lame.min.js not found", status_code=404)


def bootstrap_admin(db: Session) -> None:
    existing_admin = db.query(User).filter(User.username == settings.admin_username).first()
    if existing_admin:
        return

    user = User(
        username=settings.admin_username,
        password_hash=hash_password(settings.admin_password),
        is_admin=True,
        is_active=True,
        device_id=None,
    )
    db.add(user)
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    apply_sqlite_migrations()
    with Session(engine) as db:
        bootstrap_admin(db)


if __name__ == "__main__":
    import uvicorn

    print(f"🚗  التفريغ — Server running → http://localhost:{settings.port}")
    print(f"     Docs: http://localhost:{settings.port}/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
    )