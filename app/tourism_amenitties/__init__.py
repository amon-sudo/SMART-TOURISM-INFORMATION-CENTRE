from app.tourism_amenitties.destination.controllers.routes import (
    destination_bp
)

from app.tourism_amenitties.amenities.controllers.routes import (
    amenity_bp
)

from app.tourism_amenitties.attractions.controllers.routes import (
    attraction_bp
)

from app.tourism_amenitties.destination_translation.controllers.routes import (
    destination_translation_bp
)

from app.tourism_amenitties.attraction_translations.controllers.routes import (
    attraction_translation_bp
)

from app.tourism_amenitties.attraction_amenities.controllers.routes import (
    attraction_amenity_bp
)


def register_blueprints(app):

    app.register_blueprint(destination_bp)

    app.register_blueprint(amenity_bp)

    app.register_blueprint(attraction_bp)

    app.register_blueprint(destination_translation_bp)

    app.register_blueprint(attraction_translation_bp)

    app.register_blueprint(attraction_amenity_bp)