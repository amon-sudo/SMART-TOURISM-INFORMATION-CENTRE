from uuid import uuid4

from app.qr_code import create_app
from app.extensions import db
from app.qr_code.MVC_architecture.QR_code_views.qr_code_service import qr_code_service


app = create_app()

with app.app_context():
    db.create_all()

    target_id = uuid4()
    qr = qr_code_service.generate_or_refresh(
        target_type="itinerary",
        target_id=target_id,
        created_by=None,
        force_new=True,
    )

    client = app.test_client()

    responses = {
        "list": client.get("/admin/qr-codes"),
        "show": client.get(f"/admin/qr-codes/{qr.id}"),
        "scan": client.get(f"/public/qr/{qr.token}/scan", follow_redirects=False),
        "revoke": client.post(f"/admin/qr-codes/{qr.id}/revoke"),
        "regenerate": client.post(f"/admin/qr-codes/{qr.id}/regenerate", headers={"X-User-Id": str(uuid4())}),
    }

    for name, response in responses.items():
        body = response.get_json(silent=True)
        location = response.headers.get("Location")
        print(name, response.status_code, body if body is not None else location)

    # Verify the scan endpoint still returns a redirect target for an active QR code.
    regenerated = responses["regenerate"].get_json()["data"] if responses["regenerate"].status_code == 201 else None
    if regenerated:
        print("regenerated_qr_id", regenerated["id"])
