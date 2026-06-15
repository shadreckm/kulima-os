"""
PDF branding utilities for Kulima OS prospectus generation.
"""
import base64
from pathlib import Path
from typing import Optional

BRAND_TAGLINE = "Kulima OS — Digital Public Infrastructure Intelligence"

_LOGO_PATHS = [
    Path(__file__).resolve().parent.parent / "assets" / "logo.png",
    Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "logo.png",
]


def resolve_logo_path() -> Optional[Path]:
    for path in _LOGO_PATHS:
        if path.exists():
            return path
    return None


def logo_base64_data_uri() -> Optional[str]:
    path = resolve_logo_path()
    if not path:
        return None
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_pdf_header_html() -> str:
    """HTML header block with logo for WeasyPrint."""
    uri = logo_base64_data_uri()
    logo_img = (
        f'<img src="{uri}" alt="Kulima OS" style="height:48px;width:auto;margin-right:16px;" />'
        if uri
        else ""
    )
    return f"""
    <div style="display:flex;align-items:center;margin-bottom:8px;border-bottom:2px solid #00e676;padding-bottom:12px;">
      {logo_img}
      <div>
        <div style="font-size:22px;font-weight:bold;color:#0b2a17;">Kulima OS</div>
        <div style="font-size:11px;color:#555;letter-spacing:0.5px;">{BRAND_TAGLINE}</div>
      </div>
    </div>
    """


def draw_reportlab_header(canvas, width: float, height: float) -> float:
    """Draw branded header on ReportLab canvas. Returns y position below header."""
    from reportlab.lib.utils import ImageReader

    y = height - 50
    path = resolve_logo_path()
    if path:
        try:
            img = ImageReader(str(path))
            iw, ih = img.getSize()
            target_h = 40
            target_w = target_h * (iw / ih)
            canvas.drawImage(img, 50, y - target_h + 10, width=target_w, height=target_h, mask="auto")
            text_x = 50 + target_w + 12
        except Exception:
            text_x = 50
    else:
        text_x = 50

    canvas.setFont("Helvetica-Bold", 14)
    canvas.setFillColorRGB(0.04, 0.16, 0.09)
    canvas.drawString(text_x, y, "Kulima OS")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColorRGB(0.33, 0.33, 0.33)
    canvas.drawString(text_x, y - 12, BRAND_TAGLINE)
    canvas.setStrokeColorRGB(0, 0.9, 0.46)
    canvas.setLineWidth(2)
    canvas.line(50, y - 22, width - 50, y - 22)
    return y - 40
