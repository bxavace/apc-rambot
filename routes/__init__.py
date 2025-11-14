"""Blueprint registration helpers for the Rambot app."""

from .api import api_bp
from .admin import admin_bp
from .client import client_bp


def register_blueprints(app):
    """Attach all blueprints to the given Flask application."""
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(client_bp)


__all__ = ["register_blueprints", "api_bp", "admin_bp", "client_bp"]
