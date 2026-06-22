# SaaS Data Model

MongoDB collections and their key fields.

---

## `users`

One document per GitHub-authenticated user.

| Field            | Type   | Description                                      |
|------------------|--------|--------------------------------------------------|
| `_id`            | ObjectId | Auto-generated                                  |
| `github_id`      | int    | GitHub user ID                                   |
| `login`          | str    | GitHub username                                  |
| `email`          | str    | Primary email (from GitHub)                      |
| `avatar_url`     | str    | GitHub avatar URL                                |
| `plan`           | str    | "free" or "pro" (default: "free")               |
| `reviews_used`   | int    | PR reviews consumed this window                  |
| `reviews_limit`  | int    | PR reviews allowed per window (default: 30)      |
| `window_start`   | datetime | Start of current usage window                  |
| `extra_reviews`  | int    | Manually granted extra reviews (admin override)  |
| `created_at`     | datetime | Account creation timestamp                     |
| `updated_at`     | datetime | Last update timestamp                          |

---

## `github_installations`

One document per GitHub App installation (per org/user).

| Field              | Type   | Description                              |
|--------------------|--------|------------------------------------------|
| `_id`              | ObjectId | Auto-generated                          |
| `installation_id`  | int    | GitHub installation ID                    |
| `account_id`       | int    | GitHub account (org or user) ID          |
| `account_login`    | str    | Account login name                        |
| `account_type`     | str    | "Organization" or "User"                 |
| `repo_selection`   | str    | "selected" or "all"                      |
| `permissions`      | dict   | Granted permissions                       |
| `suspended_by`     | str | null | Suspension state                    |
| `suspended_at`     | datetime | null |                                  |
| `created_at`       | datetime | Installation timestamp                  |
| `updated_at`       | datetime | Last update timestamp                   |

---

## `repositories`

Repositories that have received at least one review.

| Field             | Type   | Description                            |
|-------------------|--------|----------------------------------------|
| `_id`             | ObjectId | Auto-generated                        |
| `github_repo_id`  | int    | GitHub repository ID                    |
| `owner`           | str    | Repository owner (org/user)            |
| `name`            | str    | Repository name                         |
| `full_name`       | str    | `owner/name`                            |
| `default_branch`  | str    | Default branch name                    |
| `is_active`       | bool   | Whether reviews are enabled             |
| `installation_id` | int    | FK to `github_installations`            |
| `created_at`      | datetime | First review timestamp                |
| `updated_at`      | datetime | Last review timestamp                  |

---

## `reviews`

One document per reviewed PR (or ad-hoc code review).

| Field           | Type   | Description                              |
|-----------------|--------|------------------------------------------|
| `_id`           | ObjectId | Auto-generated                          |
| `review_id`     | str    | UUID (matches SQLite `review_store`)     |
| `user_id`       | ObjectId | FK to `users`                          |
| `repo_id`       | ObjectId | FK to `repositories`                   |
| `github_user_id`| int    | GitHub user who triggered review         |
| `source`        | str    | "api", "cli", "github-action"           |
| `pr_number`     | int | null | PR number (null for ad-hoc)            |
| `commit_sha`    | str | null | Commit SHA                            |
| `file_path`     | str | null | Reviewed file path                     |
| `code`          | str    | Reviewed code snippet                    |
| `summary`       | str    | Natural-language summary                 |
| `risk_score`    | int    | 0–100 risk score                         |
| `verdict`       | str    | "APPROVE", "WARNING", "REQUEST_CHANGES"  |
| `issues`        | list   | Detected issues (copied from engine)     |
| `rag_used`      | bool   | Whether RAG was enabled for this review  |
| `duration_ms`   | int | null | Review duration in milliseconds      |
| `created_at`    | datetime | Review timestamp                         |

---

## `usage_events`

One document per PR review consumed (for counting/reporting).

| Field         | Type   | Description                         |
|---------------|--------|-------------------------------------|
| `_id`         | ObjectId | Auto-generated                     |
| `user_id`     | ObjectId | FK to `users`                     |
| `event_type`  | str    | "pr_review"                        |
| `source`      | str    | "github-action" or "api"           |
| `pr_number`   | int | null | PR number                       |
| `repo_full_name` | str | null | Repository name               |
| `timestamp`   | datetime | Event timestamp                   |

---

## `plans`

Tier definitions (only "free" initially; "pro" reserved for future).

| Field            | Type   | Description                             |
|------------------|--------|-----------------------------------------|
| `_id`            | ObjectId | Auto-generated                         |
| `name`           | str    | "free" or "pro"                         |
| `label`          | str    | Display label (e.g. "Free", "Pro")      |
| `pr_reviews_per_month` | int | Monthly PR review limit              |
| `max_files_per_pr` | int  | Max files processable per PR            |
| `rag_enabled`    | bool   | Whether RAG is available on this plan   |
| `price_monthly`  | float | Monthly price (0 for free)              |
| `stripe_price_id`| str | null | Stripe price ID (future)             |
| `created_at`     | datetime | Plan creation timestamp                 |

---

## `email_events`

Audit trail for all sent emails.

| Field         | Type   | Description                            |
|---------------|--------|----------------------------------------|
| `_id`         | ObjectId | Auto-generated                        |
| `to_email`    | str    | Recipient email                        |
| `template`    | str    | "welcome", "usage_guide", "limit_reached", "upgrade_prompt" |
| `subject`     | str    | Email subject line                     |
| `resend_id`   | str | null | Resend API response ID              |
| `delivered`   | bool   | Whether delivery succeeded             |
| `error`       | str | null | Error message if delivery failed      |
| `created_at`  | datetime | Send timestamp                        |
