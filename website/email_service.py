import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _resend_request(path: str, payload: dict) -> dict | None:
    import requests as req

    from website.config import Config

    api_key = Config.RESEND_API_KEY
    if not api_key:
        logger.warning("RESEND_API_KEY not set, skipping email")
        return None
    try:
        resp = req.post(
            f"https://api.resend.com/{path}",
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Resend API error: {e}")
        return None


def _log_event(user_id: str, email: str, template: str, subject: str, status: str, resend_id: str = ""):
    try:
        from website.db import get_mongo

        db, _ = get_mongo()
        db.email_events_collection.insert_one({
            "user_id": user_id,
            "email": email,
            "template": template,
            "subject": subject,
            "status": status,
            "resend_id": resend_id,
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(f"Failed to log email event: {e}")


def send_otp_email(email: str, otp: str) -> bool:
    from website.config import Config

    subject = "Your CodeSecAudit AI verification code"
    body = f"""<p>Your verification code is:</p>
<h2 style="letter-spacing: 4px; font-size: 28px; color: #6366f1;">{otp}</h2>
<p>This code expires in 10 minutes.</p>
<p>If you did not request this, you can safely ignore this email.</p>
<p>— CodeSecAudit AI Team</p>"""

    result = _resend_request("emails", {
        "from": Config.EMAIL_FROM,
        "to": [email],
        "subject": subject,
        "html": body,
    })
    success = result is not None
    _log_event("", email, "otp", subject, "sent" if success else "failed", (result or {}).get("id", ""))
    return success


def send_welcome_email(user: dict) -> bool:
    from website.config import Config

    username = user.get("username", "there")
    subject = "Welcome to CodeSecAudit AI"
    body = f"""<p>Hi {username},</p>
<p>Welcome to <strong>CodeSecAudit AI</strong>!</p>
<p>Your email has been verified and you're all set to use CodeSecAudit AI for automated security pull request reviews.</p>
<p>Here's what you get with the free plan:</p>
<ul>
  <li>30 free PR reviews per month</li>
  <li>AI-powered CWE detection</li>
  <li>Inline review comments</li>
  <li>Risk scoring</li>
  <li>RAG-guided secure coding suggestions</li>
</ul>
<p>Next step: <a href="https://github.com/apps/codesecaudit-ai/installations/new">Install the GitHub App</a> on your repository to get started.</p>
<p>— CodeSecAudit AI Team</p>"""

    result = _resend_request("emails", {
        "from": Config.EMAIL_FROM,
        "to": [user.get("email", "")],
        "subject": subject,
        "html": body,
    })
    success = result is not None
    _log_event(
        str(user.get("github_id", "")),
        user.get("email", ""),
        "welcome",
        subject,
        "sent" if success else "failed",
        (result or {}).get("id", ""),
    )
    return success


def send_usage_guide_email(user: dict) -> bool:
    logger.info(f"Usage guide email prepared for {user.get('email')} — sending delayed to 4 min after verification")
    return True


def send_limit_reached_email(user: dict) -> bool:
    from website.config import Config

    subject = "CodeSecAudit AI — Free monthly limit reached"
    body = f"""<p>Hi {user.get('username', 'there')},</p>
<p>You've used all your <strong>30 free PR reviews</strong> for this month.</p>
<p>If you need more reviews, please contact the owner:</p>
<p><a href="mailto:{Config.OWNER_CONTACT_EMAIL}?subject=Request more CodeSecAudit AI PR reviews">{Config.OWNER_CONTACT_EMAIL}</a></p>
<p>— CodeSecAudit AI Team</p>"""

    result = _resend_request("emails", {
        "from": Config.EMAIL_FROM,
        "to": [user.get("email", "")],
        "subject": subject,
        "html": body,
    })
    success = result is not None
    _log_event(
        str(user.get("github_id", "")),
        user.get("email", ""),
        "limit_reached",
        subject,
        "sent" if success else "failed",
        (result or {}).get("id", ""),
    )
    return success
