import os
import logging
from sqlalchemy import text
from app.extensions import db

logger = logging.getLogger(__name__)

def verify_environment():
    """
    Checks for essential environment variables and DB connectivity.
    """
    required_vars = ["DATABASE_URL", "STRIPE_SECRET_KEY", "GOOGLE_CLIENT_ID"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing essential environment variables: {', '.join(missing)}")
        return False
    
    try:
        # Check database connectivity
        db.session.execute(text("SELECT 1"))
        logger.info("Database connectivity verified.")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
