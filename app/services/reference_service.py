import uuid
from datetime import datetime


class ReferenceService:
    @staticmethod
    def generate(prefix: str) -> str:
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        suffix = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{stamp}-{suffix}"
