
import os, shutil, uuid, subprocess, base64
from pathlib import Path
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import List
import json

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS = BASE_DIR / "outputs"
OUTPUTS.mkdir(parents=True, exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets" / "logos"
TELIF_DIR = BASE_DIR / "telif_koruma"

# --- Auth config ---
APP_SECRET = os.environ.get("APP_SECRET", "saharaporcusu-secret")
LOGIN_USER = os.environ.get("APP_USER", "Ahmet123")
LOGIN_PASS = os.environ.get("APP_PASS", "Ahmet123")

app = FastAPI(title="SahaRaporcusu Web")
app.add_middleware(SessionMiddleware, secret_key=APP_SECRET)
app.mount("/static", StaticFiles(directory=BASE_DIR.parent / "static"), name="static")
app.mount("/logos", StaticFiles(directory=ASSETS_DIR), name="logos")
templates = Jinja2Templates(directory=BASE_DIR.parent / "templates")

def login_required(request: Request):
    return request.session.get("auth") == True

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == LOGIN_USER and password == LOGIN_PASS:
        request.session["auth"] = True
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Hatalı giriş."})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not login_required(request):
        return RedirectResponse("/login", status_code=303)
    # list logo categories & files
    cats = []
    for cat in sorted(p.name for p in ASSETS_DIR.iterdir() if p.is_dir()):
        files = sorted([f"/logos/{cat}/{x.name}" for x in (ASSETS_DIR / cat).iterdir() if x.suffix.lower() in [".png", ".jpg", ".jpeg"]])
        if files:
            cats.append({"name": cat, "files": files})
    return templates.TemplateResponse("index.html", {"request": request, "cats": cats})

# --- Telif Koruma ---
def run_telif(job_dir: Path) -> Path:
    work = job_dir / "telif"
    work.mkdir(parents=True, exist_ok=True)
    # Copy tool files
    for fname in ["telif_koruma.py", "yolov4-tiny.cfg", "yolov4-tiny.weights", "saharaporcusu.png"]:
        shutil.copy(TELIF_DIR / fname, work / fname)
    # Run script
    subprocess.run(["python", "telif_koruma.py"], cwd=work, check=True)
    out = work / "video_telif_korumali.mp4"
    if not out.exists():
        raise RuntimeError("Çıktı bulunamadı: video_telif_korumali.mp4")
    return out

@app.post("/telif", response_class=HTMLResponse)
async def telif(request: Request, video: UploadFile = File(...)):
    if not login_required(request):
        return RedirectResponse("/login", status_code=303)
    job_id = str(uuid.uuid4())[:8]
    job_dir = OUTPUTS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    vdir = job_dir / "telif"
    vdir.mkdir(parents=True, exist_ok=True)
    vpath = vdir / "video.mp4"
    with open(vpath, "wb") as f:
        f.write(await video.read())
    try:
        out = run_telif(job_dir)
        return templates.TemplateResponse("done.html", {"request": request, "title": "Telif Korumalı Video Hazır", "download_path": str(out)})
    except Exception as e:
        return templates.TemplateResponse("error.html", {"request": request, "error": str(e)})

# --- Collision (90s, 2-5 goals) ---
def save_file(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, logos: List[str] = Form(...), min_goals: int = Form(2), max_goals: int = Form(5)):
    if not login_required(request):
        return RedirectResponse("/login", status_code=303)
    # Validate & collect absolute paths
    selected = []
    for url in logos[:6]:  # limit to 6 logos
        # url like /logos/super_lig/Besiktas.png
        rel = url.split("/logos/")[-1]
        ap = ASSETS_DIR / rel
        if ap.exists():
            selected.append(str(ap))
    if not selected:
        return templates.TemplateResponse("error.html", {"request": request, "error": "Logo seçilmedi."})
    job_id = str(uuid.uuid4())[:8]
    job_dir = OUTPUTS / job_id
    out = job_dir / "saharaporcusu_video.mp4"
    # Run our generator
    subprocess.run(["python", "-u", "generator.py", "--out", str(out), "--duration", "90", "--min-goals", str(min_goals), "--max-goals", str(max_goals)] + sum([["--logo", p] for p in selected], []),
                   cwd=BASE_DIR, check=True)
    return templates.TemplateResponse("done.html", {"request": request, "title": "Gol Videosu Hazır (90 sn)", "download_path": str(out)})

@app.get("/download")
def download(path: str):
    p = Path(path)
    if not p.exists():
        return HTMLResponse("Dosya bulunamadı", status_code=404)
    return FileResponse(p, filename=p.name)
