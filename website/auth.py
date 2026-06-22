import logging
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from flask import Blueprint, redirect, request, session, url_for

from website.config import Config
from website.db import get_mongo

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/github/start")
def github_start():
    client_id = Config.GITHUB_CLIENT_ID
    if not client_id:
        return "GitHub OAuth not configured (missing GITHUB_CLIENT_ID)", 500

    redirect_uri = Config.GITHUB_CALLBACK_URL
    state = str(int(datetime.now(timezone.utc).timestamp()))
    session["oauth_state"] = state

    params = urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "read:user user:email",
    })
    url = f"https://github.com/login/oauth/authorize?{params}"
    return redirect(url)


@auth_bp.route("/auth/github/callback")
def github_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    stored_state = session.pop("oauth_state", None)

    if not code:
        return "Missing authorization code", 400

    if state and stored_state and state != stored_state:
        return "State mismatch. Possible CSRF.", 400

    access_token = _exchange_code(code)
    if not access_token:
        return "Failed to exchange authorization code", 400

    user_data = _fetch_github_user(access_token)
    if not user_data:
        return "Failed to fetch GitHub user", 400

    emails = _fetch_github_emails(access_token)
    primary_email = ""
    for e in emails:
        if e.get("primary"):
            primary_email = e.get("email", "")
            break
    if not primary_email and emails:
        primary_email = emails[0].get("email", "")

    user = _upsert_user(user_data, primary_email)
    session["user"] = {
        "github_id": str(user.get("github_id", "")),
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "avatar_url": user.get("avatar_url", ""),
        "email_verified": user.get("email_verified", False),
    }

    if not user.get("email_verified"):
        return redirect(url_for("verify_email_page"))

    return redirect(url_for("dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def _exchange_code(code: str) -> str | None:
    try:
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": Config.GITHUB_CLIENT_ID,
                "client_secret": Config.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": Config.GITHUB_CALLBACK_URL,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("access_token")
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return None


def _fetch_github_user(access_token: str) -> dict | None:
    try:
        resp = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch GitHub user: {e}")
        return None


def _fetch_github_emails(access_token: str) -> list[dict]:
    try:
        resp = requests.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch GitHub emails: {e}")
        return []


def _upsert_user(user_data: dict, email: str) -> dict:
    db, _ = get_mongo()
    github_id = str(user_data.get("id", ""))
    now = datetime.now(timezone.utc)

    existing = db.users_collection.find_one({"github_id": github_id})
    if existing:
        update = {
            "$set": {
                "username": user_data.get("login", ""),
                "email": email or existing.get("email", ""),
                "avatar_url": user_data.get("avatar_url", ""),
                "last_login_at": now,
            }
        }
        db.users_collection.update_one({"github_id": github_id}, update)
        db.users_collection.find_one({"github_id": github_id})
        existing.update({
            "username": user_data.get("login", ""),
            "email": email or existing.get("email", ""),
            "avatar_url": user_data.get("avatar_url", ""),
            "last_login_at": now,
        })
        return existing

    new_user = {
        "github_id": github_id,
        "username": user_data.get("login", ""),
        "email": email or "",
        "avatar_url": user_data.get("avatar_url", ""),
        "email_verified": False,
        "plan": "free",
        "reviews_limit": Config.FREE_PR_REVIEWS_PER_MONTH,
        "reviews_used": 0,
        "extra_reviews": 0,
        "window_start": now,
        "created_at": now,
        "last_login_at": now,
    }
    db.users_collection.insert_one(new_user)
    return new_user
