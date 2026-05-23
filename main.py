# main.py
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.utils.setup import verify_environment
import click

app = create_app()


@app.cli.command("make-admin")
@click.argument("email")
def make_admin(email):
    """Grant admin privileges to a user by email.
    Usage: flask make-admin user@example.com
    """
    from app.user_settings.models.models import User
    from app.extensions import db
    user = User.query.filter_by(email=email).first()
    if not user:
        click.echo(f"No user found with email: {email}")
        return
    user.is_admin = True
    db.session.commit()
    click.echo(f"Admin privileges granted to {email} (id={user.id})")


if __name__ == "__main__":
    with app.app_context():
        if verify_environment():
            print("--- System Ready: Environment and Database Verified ---")
            app.run(debug=True, host="0.0.0.0", port=5000)
        else:
            print("--- System Start Failed: Environment check failed. Check server logs. ---")
