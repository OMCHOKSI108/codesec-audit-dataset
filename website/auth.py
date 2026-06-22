import json
import logging
import urllib.parse
import requests
from flask import Blueprint, redirect, request, session, url_for
from website.config import Config
from website.db import upsert_user
from website.email_service import send_welcome_email

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/github/start")
def github_start():
    if not Config.GITHUB_CLIENT_ID:
        return "GitHub OAuth not configured (GITHUB_CLIENT_ID missing)", 503
    params = {
        "client_id": Config.GITHUB_CLIENT_ID,
        "redirect_uri": Config.GITHUB_CALLBACK_URL,
        "scope": "read:user user:email",
        "state": session.get("_csrf_token", ""),
    }
    url = f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"
    return redirect(url)


@auth_bp.route("/auth/github/callback")
def github_callback():
    code = request.args.get("code")
    if not code:
        return "Missing authorization code", 400

    token_data = {
        "client_id": Config.GITHUB_CLIENT_ID,
        "client_secret": Config.GITHUB_CLIENT_SECRET,
        "code": code,
    }
    try:
        tok_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data=token_data,
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if tok_resp.status_code != 200:
            return f"Token exchange failed: {tok_resp.status_code}", 502
        access_token = tok_resp.json().get("access_token")
        if not access_token:
            return "No access_token in response", 502
    except requests.RequestException as e:
        return f"Token exchange error: {e}", 502

    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.v3+json"}
    try:
        user_resp = requests.get("https://api.github.com/user", headers=headers, timeout=15)
        if user_resp.status_code != 200:
            return f"User fetch failed: {user_resp.status_code}", 502
        profile = user_resp.json()
    except requests.RequestException as e:
        return f"User fetch error: {e}", 502

    try:
        email_resp = requests.get("https://api.github.com/user/emails", headers=headers, timeout=15)
        emails = email_resp.json() if email_resp.status_code == 200 else []
        primary = next((e["email"] for e in emails if e.get("primary")), profile.get("email", ""))
    except requests.RequestException:
        primary = profile.get("email", "")

    user_data = {
        "username": profile.get("login", ""),
        "name": profile.get("name", "") or profile.get("login", ""),
        "email": primary,
        "avatar_url": profile.get("avatar_url", ""),
        "plan": "free",
        "reviews_limit": Config.FREE_PR_REVIEWS_PER_MONTH,
        "extra_reviews": 0,
    }

    user = upsert_user(str(profile["id"]), user_data)
    was_new = user.get("created_at") == user.get("last_login_at")
    session["user"] = {
        "github_id": str(profile["id"]),
        "username": user["username"],
        "name": user.get("name", user["username"]),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url", ""),
        "plan": user.get("plan", "free"),
        "reviews_limit": user.get("reviews_limit", Config.FREE_PR_REVIEWS_PER_MONTH),
        "reviews_used": user.get("reviews_used", 0),
        "extra_reviews": user.get("extra_reviews", 0),
    }

    if was_new:
        send_welcome_email(user)

    return redirect(url_for("dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
