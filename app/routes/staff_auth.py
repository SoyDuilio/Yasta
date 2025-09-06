# app/routes/staff_auth.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templating import templates

router = APIRouter(tags=["Staff Authentication"])

@router.get("/staff/login", response_class=HTMLResponse, name="staff_login_page")
async def serve_staff_login_page(request: Request):
    """Muestra la página de inicio de sesión para el personal de YASTA."""
    return templates.TemplateResponse("auth/staff_login.html", {"request": request})

# No olvides incluir este nuevo router en tu main.py