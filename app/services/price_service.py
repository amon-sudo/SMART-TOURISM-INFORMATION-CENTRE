from app.models.attraction import Attraction


class PriceService:
    @staticmethod
    def get_unit_price(target_type: str, target_id) -> float:
        if target_type == "attraction":
            attraction = Attraction.query.get(target_id)
            if attraction is None:
                return 0.0
            return float(getattr(attraction, "entry_fee", 0.0) or 0.0)

        if target_type == "accommodation":
            from app.tourism_amenitties.accommodation.models.accommodation import Accommodation, RoomType
            acc = Accommodation.query.get(target_id)
            if acc is None:
                return 0.0
            prices = [r.base_price for r in acc.rooms if r.base_price is not None]
            return float(min(prices)) if prices else 0.0

        if target_type == "tour_package":
            from app.tourism_amenitties.tours.models.tour_package import TourPackage
            pkg = TourPackage.query.get(target_id)
            if pkg is None:
                return 0.0
            return float(getattr(pkg, "price_per_person", 0.0) or 0.0)

        if target_type == "transport":
            from app.transport_feature.Transport_schedule.MVC_architecture.transport_schedule_models.transport_schedule_domain import transport_schedule
            schedule = transport_schedule.query.get(target_id)
            if schedule is None:
                return 0.0
            return float(getattr(schedule, "price", 0.0) or 0.0)

        return 0.0
