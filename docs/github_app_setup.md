# GitHub App Setup

CodeSecAudit AI uses the **GitHub App Manifest flow** to create its GitHub App without manually filling every field in the GitHub UI.

---

## Prerequisites

- Python 3.10+
- `requests` library (`pip install requests`)
- A GitHub account

---

## Quick Setup

### 1. Generate the manifest

```bash
python scripts/create_github_app_manifest.py
```

This prints a URL. Open it in your browser.

> For an organization, use:
> ```bash
> python scripts/create_github_app_manifest.py --org YOUR_ORG_NAME
> ```

Required callback/webhook URLs can be passed as args:

```bash
python scripts/create_github_app_manifest.py \
  --callback-url https://your-website.onrender.com/auth/github/callback \
  --webhook-url https://your-api.onrender.com/webhook/github
```

Or set env vars:

```bash
export GITHUB_CALLBACK_URL=https://your-website.onrender.com/auth/github/callback
export GITHUB_WEBHOOK_URL=https://your-api.onrender.com/webhook/github
```

### 2. Create the app in GitHub

1. Open the printed URL in your browser.
2. Review the pre-filled fields.
3. Click **"Create GitHub App"**.
4. GitHub redirects to the `redirect_url` with a `?code=...` parameter.
5. Copy the `code` value from the URL.

### 3. Exchange the code for credentials

```bash
python scripts/complete_github_app_manifest.py --code YOUR_TEMP_CODE
```

This:

- Calls `POST /app-manifests/{code}/conversions`
- Saves credentials to `secrets/github_app_credentials.local.json`
- Prints the App ID, slug, and Client ID
- Shows safe `.env` template

### 4. Apply credentials to `.env`

Dry-run first:

```bash
python scripts/apply_github_app_env.py
```

To write:

```bash
python scripts/apply_github_app_env.py --write
```

This sets:

```text
GITHUB_APP_ID
GITHUB_APP_SLUG
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GITHUB_WEBHOOK_SECRET
GITHUB_PRIVATE_KEY_BASE64
```

### 5. Verify

```bash
python scripts/verify_github_app_env.py
```

---

## Permissions

| Permission | Level | Why |
|------------|-------|-----|
| **Contents** | Read | Read PR file contents for review |
| **Pull requests** | Read & write | Post summary comments and inline review comments |
| **Issues** | Read & write | Post review results as issue comments |
| **Checks** | Read & write | Create check runs for status visibility |
| **Metadata** | Read | Access repo metadata for PR context |

## Events

| Event | Why |
|-------|-----|
| **Pull request** | Trigger review on `opened` and `synchronize` |
| **Installation** | Track which repos the app is installed on |
| **Installation repositories** | Track repo additions/removals |

## Security

- **Never commit** the private key (`.pem` file)
- **Never commit** `.env`
- **Never commit** `secrets/github_app_credentials.local.json`
- Keep the webhook secret private
- Store secrets in Render environment variables (not in the repo)

## Render Deployment

Set these env vars on your Render services:

| Variable | Service | Description |
|----------|---------|-------------|
| `GITHUB_APP_ID` | API, Website | GitHub App numeric ID |
| `GITHUB_APP_SLUG` | Website | App slug for install button URL |
| `GITHUB_CLIENT_ID` | Website | GitHub OAuth Client ID |
| `GITHUB_CLIENT_SECRET` | Website | GitHub OAuth Client Secret |
| `GITHUB_WEBHOOK_SECRET` | API | Webhook secret for payload verification |
| `GITHUB_PRIVATE_KEY_BASE64` | API | Base64-encoded App private key |
| `GITHUB_CALLBACK_URL` | Website | Full callback URL (`https://website/auth/github/callback`) |
| `GITHUB_WEBHOOK_URL` | API | Full webhook URL (`https://api/webhook/github`) |

---

## Next Steps

- GitHub App webhook review processing is the next backend phase
- The manifest scripts handle **registration only**
- Install the app on a repo after creation to enable webhook delivery
