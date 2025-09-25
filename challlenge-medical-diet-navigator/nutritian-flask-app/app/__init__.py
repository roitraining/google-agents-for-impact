# app/__init__.py
from flask import Flask, render_template
from config import Config  # Or dynamically choose config based on FLASK_ENV


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'website-secret-key2'

    # Register blueprints
    from .routes.home import home_bp
    app.register_blueprint(home_bp)

    # ✅ Global error handler for ANY uncaught exception
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.exception("Unhandled Exception: %s", e)
        return render_template("error.html", error_message=str(e)), 500
    

    return app
