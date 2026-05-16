"""
Marshmallow schemas for handoff endpoints.
"""

from marshmallow import Schema, fields, validates, ValidationError


class HandoffCreateSchema(Schema):
    """
    Validates POST /api/sessions/<id>/handoff body.

    session_state is an open dict — the kiosk can include any fields
    that represent the current tourist interaction. The required keys
    listed below are the minimum the mobile app needs to resume.
    """
    session_state = fields.Dict(
        required=True,
        metadata={"description": "Full serialised kiosk UI state"},
    )

    @validates("session_state")
    def validate_session_state(self, value, **kwargs):
        required_keys = {"step", "destination", "language"}
        missing = required_keys - set(value.keys())
        if missing:
            raise ValidationError(
                f"session_state is missing required keys: {', '.join(missing)}. "
                f"Required: step, destination, language."
            )
        if not isinstance(value.get("step"), str):
            raise ValidationError("session_state.step must be a string")
