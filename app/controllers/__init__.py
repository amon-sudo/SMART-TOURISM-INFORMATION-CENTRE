"""Legacy controller shims.

The kiosk module's routes import ``app.controllers.kiosk_controllers``;
the real controllers live under ``app.kiosk_feature.kiosk.MVC_architecture``.
This shim re-exports them so the existing imports work without churn.
"""
