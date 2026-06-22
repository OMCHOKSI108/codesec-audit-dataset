import logging
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, redirect, render_template, request, session, url_for

from website.api_client import fetch_reviews
from website.auth import auth_bp
from website.config import Config
from website.email_service import send_welcome_email
from website.github_app import install_url
from website.otp import OTPError, send_otp, verify_otp
from website.usage import get_usage

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = config_class.SESSION_SECRET

    app.register_blueprint(auth_bp)

    _inject_global_context(app)

    @app.route("/")
    def index():
        return render_template("index.html", install_github_url=install_url())

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/verify-email")
    def verify_email_page():
        user = session.get("user")
        if not user:
            return redirect(url_for("login"))
        return render_template("verify_email.html", email=user.get("email", ""))

    @app.route("/otp/send", methods=["POST"])
    def otp_send():
        user = session.get("user")
        if not user:
            return {"error": "Not logged in"}, 401

        email = user.get("email", "")
        if not email:
            return {"error": "No email address on file"}, 400

        try:
            send_otp(user["github_id"], email)
            return {"success": True, "message": "Verification code sent"}
        except OTPError as e:
            return {"error": str(e)}, 429
        except Exception as e:
            logger.exception("OTP send failed")
            return {"error": "Failed to send verification code. Please try again."}, 500

    @app.route("/otp/verify", methods=["POST"])
    def otp_verify():
        user = session.get("user")
        if not user:
            return {"error": "Not logged in"}, 401

        otp = request.form.get("otp", "")
        if not otp:
            return {"error": "Missing verification code"}, 400

        try:
            verify_otp(user["github_id"], otp)
            session["user"]["email_verified"] = True
            try:
                send_welcome_email(user)
            except Exception:
                logger.warning("Welcome email send failed, continuing")
            return {"success": True, "message": "Email verified", "redirect": url_for("auth.dashboard")}
        except OTPError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.exception("OTP verify failed")
            return {"error": "Verification failed. Please try again."}, 500

    @app.route("/dashboard")
    def dashboard():
        user = session.get("user")
        if not user:
            return redirect(url_for("login"))

        if not user.get("email_verified"):
            return redirect(url_for("verify_email_page"))

        db, _ = _get_db()
        user_doc = db.users_collection.find_one({"github_id": user["github_id"]})
        usage = get_usage(user_doc)

        reviews = fetch_reviews(Config.CODESEC_API_URL, limit=10)

        return render_template(
            "dashboard.html",
            user=user_doc or user,
            usage=usage,
            reviews=reviews[:5],
            install_github_url=install_url(),
        )

    @app.route("/reviews")
    def reviews():
        user = session.get("user")
        if not user:
            return redirect(url_for("login"))

        reviews_list = fetch_reviews(Config.CODESEC_API_URL, limit=50)
        return render_template("reviews.html", reviews=reviews_list)

    @app.route("/usage")
    def usage():
        user = session.get("user")
        user_doc = None
        if user:
            db, _ = _get_db()
            user_doc = db.users_collection.find_one({"github_id": user["github_id"]})
        usage_data = get_usage(user_doc)
        return render_template("usage.html", usage=usage_data, user=user_doc or user)

    @app.route("/repos")
    def repos():
        user = session.get("user")
        if not user:
            return redirect(url_for("login"))
        return render_template("repos.html", install_github_url=install_url())

    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    @app.route("/settings")
    def settings():
        user = session.get("user")
        if not user:
            return redirect(url_for("login"))

        db, _ = _get_db()
        user_doc = db.users_collection.find_one({"github_id": user["github_id"]})
        return render_template("settings.html", user=user_doc or user)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, message="Internal server error"), 500

    return app


def _get_db():
    from website.db import get_mongo

    return get_mongo()


def _inject_global_context(app):
    @app.context_processor
    def inject_globals():
        user = session.get("user")
        return {
            "app_name": Config.APP_NAME,
            "current_year": datetime.now(timezone.utc).year,
            "user": user,
            "logged_in": user is not None,
        }


app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=5000)
