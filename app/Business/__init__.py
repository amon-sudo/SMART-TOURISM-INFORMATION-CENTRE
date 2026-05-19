from flask import Flask


def register_business_blueprints(app: Flask) -> None:
	"""Register all Business module blueprints in one place.
	
	Note: Business blueprints define their own url_prefix internally,
	so we register them without an additional prefix here.
	"""
	# Business Registration blueprints
	try:
		from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_registration_routes import (
			business_bp,
		)
		from app.Business.Business_registration.MVC_architecture_business.Business_controllers.Business_registration_routes_admin import (
			business_admin_blueprint,
		)
		app.register_blueprint(business_bp)
		app.register_blueprint(business_admin_blueprint)
	except ModuleNotFoundError as exc:
		app.logger.warning("Skipping business registration blueprints: %s", exc)

	# Business Profile blueprints
	try:
		from app.Business.Business_Profile.MVC_architecture.Business_profile_Controllers.Business_profile_routes import (
			business_bp as business_profile_blueprint,
		)
		from app.Business.Business_Profile.MVC_architecture.Business_profile_Controllers.Business_profile_admin_routes import (
			business_admin_blueprint as business_profile_admin_blueprint,
		)
		app.register_blueprint(business_profile_blueprint)
		app.register_blueprint(business_profile_admin_blueprint)
	except Exception as exc:
		app.logger.warning("Skipping business profile blueprints: %s", exc)
