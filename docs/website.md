# CodeSecAudit AI — SaaS Website

Flask-based marketing site + dashboard with GitHub OAuth login.

---

## Local Run

```bash
pip install -e ".[website]"
flask --app website.app run --port 5000
# or
python -m website.app
```

Open http://localhost:5000

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CODESEC_API_URL` | No | FastAPI backend URL (default: `http://localhost:8000`) |
| `PUBLIC_WEBSITE_URL` | No | Public website URL (default: `http://localhost:5000`) |
| `GITHUB_CLIENT_ID` | For OAuth | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | For OAuth | GitHub OAuth App client secret |
| `GITHUB_CALLBACK_URL` | No | OAuth callback (default: `<PUBLIC_WEBSITE_URL>/auth/github/callback`) |
| `SESSION_SECRET` | For production | Flask session secret key |
| `GITHUB_APP_SLUG` | No | GitHub App slug for install button |
| `MONGODB_URI` | No | MongoDB connection string |
| `MONGODB_DB_NAME` | No | MongoDB database name (default: `codesec_audit`) |
| `RESEND_API_KEY` | No | Resend API key for welcome emails |
| `EMAIL_FROM` | No | From address for emails |
| `OWNER_CONTACT_EMAIL` | No | Contact email (default: `omchoksi108@gmail.com`) |
| `FREE_PR_REVIEWS_PER_MONTH` | No | Free plan limit (default: `30`) |

## GitHub OAuth Setup

1. Go to **Settings → Developer settings → OAuth Apps → New OAuth App**
2. Fill:
   - Application name: `CodeSecAudit AI (Dev)`
   - Homepage URL: `http://localhost:5000` or your Render URL
   - Authorization callback URL: `http://localhost:5000/auth/github/callback` or your Render URL
3. Copy `Client ID` and `Client Secret`
4. Set as `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` env vars

## Render Deployment

1. Create a new **Web Service** in Render dashboard
2. Connect your repo
3. Set:
   - **Name:** `codesec-website`
   - **Region:** same as API
   - **Branch:** `main`
   - **Runtime:** Docker
   - **Dockerfile path:** `deploy/render/website.Dockerfile`
   - **Health Check Path:** `/`
4. Add all env vars from the table above
5. Deploy

Or use the `render.yaml` blueprint for automated setup.

## MongoDB Behavior

- If `MONGODB_URI` is set and reachable: user profiles are stored in MongoDB `users` collection
- If MongoDB is unavailable/unconfigured: in-memory dict fallback (lost on restart)
- Website never crashes due to DB issues

## Resend Welcome Email

- If `RESEND_API_KEY` is set: welcome email sent on first sign-in
- Email uses Resend HTTP API directly (no SDK needed)
- If email fails, login still succeeds (logged warning)

## Limitations

- Usage enforcement is **display-only**; actual limit checking is next step
- GitHub App install button appears if `GITHUB_APP_SLUG` is set; no webhook yet
- No account settings persistence (coming in next iteration)
- Review history depends on FastAPI backend availability
