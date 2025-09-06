# app/routes/demos.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templating import templates

router = APIRouter(prefix="/demos", tags=["Reportes Demo"])

@router.get("/comercial", response_class=HTMLResponse, name="demo_comercial")
async def serve_demo_comercial(request: Request):
    return templates.TemplateResponse("demos/demo_comercial.html", {"request": request})

@router.get("/servicios", response_class=HTMLResponse, name="demo_servicios")
async def serve_demo_servicios(request: Request):
    return templates.TemplateResponse("demos/demo_servicios.html", {"request": request})

@router.get("/productivo", response_class=HTMLResponse, name="demo_productivo")
async def serve_demo_productivo(request: Request):
    return templates.TemplateResponse("demos/demo_productivo.html", {"request": request})