from app.models.attraction import Attraction


class PriceService:
    @staticmethod
    def get_unit_price(target_type: str, target_id) -> float:
        # Minimal fallback pricing for unsupported targets in this codebase.
        if target_type == "attraction":
            attraction = Attraction.query.get(target_id)
            if attraction is None:
                return 0.0
            return float(getattr(attraction, "entry_fee", 0.0) or 0.0)
        return 0.0
