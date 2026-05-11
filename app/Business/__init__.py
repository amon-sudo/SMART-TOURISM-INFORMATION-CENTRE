from flask import Flask


def register_business_blueprints(app: Flask) -> None:
	"""Register all Business module blueprints in one place."""
	from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_registrationroutes import (
		business_bp,
	)
	from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_registration_routes_admin import (
		business_admin_bp,
	)

	from app.Business.Business_Profile.MVC_architecture.Business_profile_Controllers.Business_profile_routes import (
		business_profile_blueprint,
	)
	from app.Business.Business_Profile.MVC_architecture.Business_profile_Controllers.Business_admin_routes import (
		business_admin_blueprint,
	)

	app.register_blueprint(business_bp)
	app.register_blueprint(business_admin_bp)
	app.register_blueprint(business_profile_blueprint)
	app.register_blueprint(business_admin_blueprint)
