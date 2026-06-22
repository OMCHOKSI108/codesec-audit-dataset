import os
import logging
from flask import Flask, render_template, session, redirect, url_for

from website.config import Config
from website.auth import auth_bp
from website.api_client import fetch_reviews, fetch_stats
from website.usage import get_usage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_globals():
        slug = Config.GITHUB_APP_SLUG
        return {
            "github_app_url": f"https://github.com/apps/{slug}/installations/new" if slug else "",
            "owner_email": Config.OWNER_CONTACT_EMAIL,
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        if session.get("user"):
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard():
        user = session.get("user")
        if not user:
            return redirect(url_for("login_page"))
        usage = get_usage(user)
        reviews = []
        try:
            reviews = fetch_reviews(limit=5)
        except Exception:
            pass
        return render_template("dashboard.html", usage=usage, reviews=reviews)

    @app.route("/reviews")
    def reviews_page():
        error = None
        reviews = []
        try:
            reviews = fetch_reviews(limit=100)
        except Exception as e:
            error = f"Could not load reviews from API: {e}"
        return render_template("reviews.html", reviews=reviews, error=error)

    @app.route("/usage")
    def usage_page():
        user = session.get("user")
        usage = get_usage(user)
        return render_template("usage.html", usage=usage)

    @app.route("/contact")
    def contact_page():
        return render_template("contact.html")

    @app.route("/settings")
    def settings_page():
        if not session.get("user"):
            return redirect(url_for("login_page"))
        return render_template("settings.html")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", error="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", error="Internal server error"), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
