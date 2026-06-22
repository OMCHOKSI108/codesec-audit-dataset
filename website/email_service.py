import logging
import requests
from website.config import Config

logger = logging.getLogger(__name__)


def send_welcome_email(user: dict) -> bool:
    if not Config.RESEND_API_KEY:
        logger.info("RESEND_API_KEY not set, skipping welcome email")
        return False
    email = user.get("email", "")
    username = user.get("username", "there")
    if not email:
        logger.info("No email available, skipping welcome email")
        return False
    to_name = user.get("name", "") or username
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {Config.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": Config.EMAIL_FROM or "CodeSecAudit <onboarding@resend.dev>",
                "to": [email],
                "subject": "Welcome to CodeSecAudit AI — your PRs are now protected",
                "html": _build_welcome_html(to_name),
            },
            timeout=15,
        )
        if resp.status_code in (200, 201):
            logger.info("Welcome email sent to %s", email)
            return True
        logger.warning("Welcome email failed: %s %s", resp.status_code, resp.text[:200])
    except requests.RequestException as e:
        logger.warning("Welcome email request failed: %s", e)
    return False


def _build_welcome_html(name: str) -> str:
    dashboard_url = f"{Config.PUBLIC_WEBSITE_URL}/dashboard"
    return f"""<!DOCTYPE html>
<html><body style="font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:20px">
<h2>Welcome to CodeSecAudit AI, {name}!</h2>
<p>Your pull requests are now protected by OWASP-based security review.</p>
<ul>
  <li><strong>30 free PR reviews</strong> per month</li>
  <li>Automated CWE detection</li>
  <li>Inline comments and risk scoring</li>
  <li>RAG-powered fix suggestions</li>
</ul>
<p><a href="{dashboard_url}" style="display:inline-block;padding:12px 24px;background:#2563eb;color:#fff;text-decoration:none;border-radius:6px">Go to Dashboard</a></p>
<p style="color:#666;font-size:13px">Contact <a href="mailto:{Config.OWNER_CONTACT_EMAIL}">{Config.OWNER_CONTACT_EMAIL}</a> for questions.</p>
</body></html>"""
