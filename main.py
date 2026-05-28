from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database.connection import Base, engine, SessionLocal
from app.database.migrate import run_light_migrations
from app.middleware.rate_limit import limiter
from app.routers import (
    achievements,
    admin,
    auth,
    chat,
    formulas,
    lessons,
    math,
    notifications,
    progress,
    teacher,
    tests,
)
from app.services.seed_service import seed_database

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_light_migrations(engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Calculus Visual Learning",
    description="Интерактивная система визуального изучения производных и интегралов",
    version="2.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

app.include_router(auth.router)
app.include_router(math.router)
app.include_router(lessons.router)
app.include_router(tests.router)
app.include_router(admin.router)
app.include_router(formulas.router)
app.include_router(achievements.router)
app.include_router(progress.router)
app.include_router(teacher.router)
app.include_router(notifications.router)
app.include_router(chat.router)

PAGES = {
    "/": "index.html",
    "/graphs": "graphs.html",
    "/derivatives": "derivatives.html",
    "/integrals": "integrals.html",
    "/limits": "limits.html",
    "/learning": "learning.html",
    "/calculator": "calculator.html",
    "/login": "login.html",
    "/register": "register.html",
    "/forgot-password": "forgot_password.html",
    "/reset-password": "reset_password.html",
    "/admin": "admin.html",
    "/teacher": "teacher.html",
    "/profile": "profile.html",
    "/chat": "chat.html",
}


def render_page(request: Request, template_name: str):
    return templates.TemplateResponse(
        template_name,
        {"request": request, "page": template_name.replace(".html", "")},
    )


for route, template in PAGES.items():

    @app.get(route, response_class=HTMLResponse, name=route)
    async def page_handler(request: Request, tpl=template):
        return render_page(request, tpl)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
