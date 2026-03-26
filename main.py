from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="ASX Intel")

# Serve static files (CSS, JS) from the /static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 looks for HTML templates in the /templates folder
templates = Jinja2Templates(directory="templates")

# Import the analysis router — all /analyse logic lives there
from routers.analyse import router as analyse_router
app.include_router(analyse_router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works(request: Request):
    """Serve the How It Works architecture page."""
    return templates.TemplateResponse("howitworks.html", {"request": request})
