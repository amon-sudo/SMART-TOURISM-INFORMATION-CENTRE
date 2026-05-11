# app/__init__.py
"""
Outer initializer for the Smart Tourism app.
Delegates to app/authanduser/__init__.py where create_app() is defined.
"""

from app.authanduser import create_app

# Expose create_app so main.py can import it directly
__all__ = ["create_app"]
