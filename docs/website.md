# CodeSecAudit AI — Website

Flask SaaS website for CodeSecAudit AI — the product portal where users sign in with GitHub, verify email via OTP, view usage, and install the GitHub App.

## Pages

| Route | Page | Auth Required | Email Verified |
|-------|------|---------------|----------------|
| `/` | Landing page | No | - |
| `/login` | Sign in | No | - |
| `/auth/github/start` | OAuth start | No | - |
| `/auth/github/callback` | OAuth callback | No | - |
| `/verify-email` | Email OTP | Yes | No |
| `/dashboard` | Usage dashboard | Yes | Yes |
| `/reviews` | Review history | Yes | Yes |
| `/usage` | Usage details | Yes | Yes |
| `/repos` | Connected repos | Yes | Yes |
| `/settings` | Account settings | Yes | Yes |
| `/contact` | Contact owner | No | - |

## Local Run

```bash
pip install -e ".[website]"
flask --app website.app run --port 5000
```

Open http://localhost:5000

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PUBLIC_WEBSITE_URL` | No | `http://localhost:5000` | Public URL for OAuth redirect |
| `CODESEC_API_URL` | No | `https://codesec-api.onrender.com` | FastAPI backend URL |
| `GITHUB_CLIENT_ID` | Yes | (empty) | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | Yes | (empty) | GitHub OAuth App client secret |
| `GITHUB_CALLBACK_URL` | No | auto-derived | OAuth callback URL |
| `GITHUB_APP_SLUG` | No | `codesecaudit-ai` | GitHub App slug for install button |
| `SESSION_SECRET` | Yes | (empty) | Flask session signing key |
| `MONGODB_URI` | No | (empty) | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | No | `codereview` | MongoDB database name |
| `RESEND_API_KEY` | No | (empty) | Resend.com API key for email |
| `EMAIL_FROM` | No | `CodeSecAudit AI <onboarding@resend.dev>` | Sender email address |
| `OWNER_CONTACT_EMAIL` | No | `omchoksi108@gmail.com` | Owner support email |
| `FREE_PR_REVIEWS_PER_MONTH` | No | `30` | Monthly free PR review limit |

### Fallbacks

- `GITHUB_CLIENT_ID` falls back to `GITHUB_APP_CLIENT_ID`
- `GITHUB_CLIENT_SECRET` falls back to `GITHUB_APP_CLIENT_SECRET`
- `EMAIL_FROM` falls back to Resend default sender

## GitHub OAuth Setup

1. Go to your GitHub App settings: https://github.com/settings/apps/codesecaudit-ai
2. Under **Identifying and authorizing users**, set:
   - **Callback URL**: `https://codesec-website.onrender.com/auth/github/callback` (production) or `http://localhost:5000/auth/github/callback` (local)
3. The app's Client ID and Client Secret are used for OAuth

The GitHub App's OAuth credentials are reused for the website. Alternatively, you can create a separate GitHub OAuth App.

## OTP Verification Flow

1. User signs in with GitHub
2. If email not verified, redirected to `/verify-email`
3. Click "Send Verification Code" → OTP sent via Resend
4. Enter 6-digit code → code verified against SHA-256 hash
5. Email marked verified, welcome email sent, redirected to dashboard

OTP constraints:
- 6-digit numeric, expires in 10 minutes
- Max 3 send attempts per 10 minutes
- Max 3 verify attempts per OTP
- OTP stored as SHA-256 hash, never plaintext

## Resend Email

Emails are sent via Resend API. Templates:

| Template | Trigger | Contents |
|----------|---------|----------|
| OTP | `/otp/send` | 6-digit verification code |
| Welcome | After OTP verify | Getting started + install CTA |
| Usage Guide | Designed only | Not scheduled |
| Limit Reached | When limit hit | Contact owner link |

If Resend API key is not set, emails silently skip instead of crashing.

## MongoDB Collections

### `users`
```json
{
  "github_id": "12345",
  "username": "octocat",
  "email": "octocat@github.com",
  "avatar_url": "https://avatars.githubusercontent.com/u/12345",
  "email_verified": false,
  "plan": "free",
  "reviews_limit": 30,
  "reviews_used": 0,
  "extra_reviews": 0,
  "window_start": "2026-06-22T00:00:00+00:00",
  "created_at": "2026-06-22T00:00:00+00:00",
  "last_login_at": "2026-06-22T00:00:00+00:00"
}
```

### `email_otps`
```json
{
  "user_id": "12345",
  "email": "octocat@github.com",
  "otp_hash": "sha256hex...",
  "expires_at": "2026-06-22T00:10:00+00:00",
  "attempts": 0,
  "created_at": "2026-06-22T00:00:00+00:00"
}
```

### `email_events`
```json
{
  "user_id": "12345",
  "email": "octocat@github.com",
  "template": "welcome | otp | usage_guide | limit_reached",
  "subject": "...",
  "status": "sent | failed",
  "resend_id": "...",
  "created_at": "2026-06-22T00:00:00+00:00"
}
```

## Graceful Degradation

- **MongoDB unavailable**: Falls back to in-memory storage (data lost on restart)
- **Resend unavailable**: Email sending skipped, no crash
- **FastAPI unavailable**: Reviews page shows empty state gracefully

## Render Deployment

The website is deployed as a separate Render web service.

### render.yaml

```yaml
- type: web
  name: codesec-website
  env: docker
  dockerfilePath: ./deploy/render/website.Dockerfile
  dockerContext: .
```

### Service configuration

Set these env vars in Render dashboard (or via API):

- `PUBLIC_WEBSITE_URL` — `https://codesec-website.onrender.com`
- `CODESEC_API_URL` — `https://codesec-api.onrender.com`
- `GITHUB_CLIENT_ID` — From GitHub App settings
- `GITHUB_CLIENT_SECRET` — From GitHub App settings
- `GITHUB_CALLBACK_URL` — `https://codesec-website.onrender.com/auth/github/callback`
- `GITHUB_APP_SLUG` — `codesecaudit-ai`
- `SESSION_SECRET` — Random secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
- `MONGODB_URI` — MongoDB Atlas connection string
- `MONGODB_DB_NAME` — `codereview`
- `RESEND_API_KEY` — From Resend.com
- `EMAIL_FROM` — Sender address
- `OWNER_CONTACT_EMAIL` — `omchoksi108@gmail.com`
- `FREE_PR_REVIEWS_PER_MONTH` — `30`

### Manual deploy

```bash
render deploy
```

Or via API:
```bash
curl -X POST https://api.render.com/v1/services/{service_id}/deploys \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

## Limitations

- Usage tracking is **display-only** — webhook enforcement is not yet implemented
- GitHub App installation status shows as not-connected until the webhook integration is complete
- 4-minute delayed usage guide email is designed but not scheduled
- Streamlit dashboard remains available alongside the Flask website
- In-memory fallback loses data on restart (MongoDB required for persistence)
- Account management features (password change, subscription management) are future work
