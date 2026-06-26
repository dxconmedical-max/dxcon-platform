from pathlib import Path

files = {
"app/api/box_qr/routes.py": r'''
from flask import Blueprint
from app.models.transport_box import TransportBox
from app.core.qr_service import box_qr_payload

box_qr_bp = Blueprint(
    "box_qr",
    __name__,
    url_prefix="/api/v1/box-qr"
)


@box_qr_bp.route("/<box_id>")
def get_box_qr(box_id):
    box = TransportBox.query.get(box_id)

    if not box:
        box = TransportBox.query.filter_by(
            box_code=box_id
        ).first()

    if not box:
        return {"success": False, "error": "box not found"}, 404

    return {
        "success": True,
        "box_id": box.id,
        "box_code": box.box_code,
        "qr_payload": box_qr_payload(box.box_code)
    }
''',

"app/web/box_qr.py": r'''
from flask import Blueprint
from app.models.transport_box import TransportBox
from app.core.qr_service import box_qr_payload

box_qr_web_bp = Blueprint("box_qr_web", __name__)


@box_qr_web_bp.route("/boxes/<box_id>/qr")
def box_qr_page(box_id):
    box = TransportBox.query.get(box_id)

    if not box:
        box = TransportBox.query.filter_by(
            box_code=box_id
        ).first()

    if not box:
        return "Box not found", 404

    payload = box_qr_payload(box.box_code)

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;text-align:center;">
        <h1>Transport Box QR</h1>
        <h2>{box.box_code}</h2>

        <div style="font-size:24px;background:white;padding:30px;border-radius:12px;display:inline-block;border:2px dashed #0d6efd;">
            {payload}
        </div>

        <p>Collector/Lab app sẽ scan payload này để xác nhận đúng box.</p>

        <br>
        <a href="/transport-boxes">Back to Boxes</a> |
        <a href="/logistics-v2">Logistics V2</a>
    </body>
    </html>
    """
'''
}

for name, content in files.items():
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n")
    print("wrote", name)

init = Path("app/__init__.py")
text = init.read_text()

for imp in [
    "from app.api.box_qr.routes import box_qr_bp\n",
    "from app.web.box_qr import box_qr_web_bp\n",
]:
    if imp not in text:
        text = imp + text

for reg in [
    "    app.register_blueprint(box_qr_bp)\n",
    "    app.register_blueprint(box_qr_web_bp)\n",
]:
    if reg.strip() not in text:
        text = text.replace("    return app", reg + "    return app")

init.write_text(text)
print("registered box QR module")
