"""
Authentication Models
To maintain the MVC architecture without crashing the database with duplicate table mappings, 
we import the unified core models here. The single source of truth remains in user_settings, 
but the authanduser module can still access its 'M' (Models) from this file.
"""

from app.user_settings.models.models import User, RefreshToken, PasswordReset
