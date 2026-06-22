# Email Workflows

Transactional emails are sent via [Resend](https://resend.com).

---

## 1. Welcome Email

**Trigger**: User completes GitHub App installation (or signs up via the web app).

**Delay**: Immediate (sent on first webhook or signup confirmation).

**Subject**: `Welcome to CodeSecAudit AI — your PRs are now protected`

**Content**:
- Thank you for installing CodeSecAudit AI.
- Brief feature overview (7 CWE detectors, inline comments, risk scoring).
- Link to dashboard showing first review results.
- Note on free tier limits (30 PR reviews/month).
- Owner contact: `omchoksi108@gmail.com`.

---

## 2. Usage Guide Email

**Trigger**: 4 minutes after the user's first completed PR review.

**Delay**: 4 minutes (allows time for the user to see their first review).

**Subject**: `Getting started with CodeSecAudit AI`

**Content**:
- How to interpret review results (risk score, verdicts).
- How to enable optional RAG (if on Pro plan).
- Link to docs.
- How to configure rules in `codesec.yml` (future).
- How to contact support.

---

## 3. Limit Reached Email

**Trigger**: User hits `reviews_used >= reviews_limit` (i.e., 30/30 reviews).

**Delay**: Immediate (on block).

**Subject**: `CodeSecAudit AI — you've used all your free PR reviews`

**Content**:
- "You've used all 30 free PR reviews for this 30-day window."
- Current usage: `reviews_used / reviews_limit`.
- Reset date: `window_start + 30 days`.
- CTA: "Need more reviews?" — mailto link to owner.
- Owner contact: `mailto:omchoksi108@gmail.com?subject=CodeSecAudit%20-%20Upgrade%20Request`.

---

## 4. Manual Upgrade / Contact Owner

**Trigger**: User clicks the contact link in the limit-reached email or on the
dashboard.

**Mechanism**: Simple `mailto:omchoksi108@gmail.com` link with pre-filled
subject line. No in-app purchase flow yet.

**Subject** (pre-filled): `CodeSecAudit - Upgrade Request`

**Content** (user writes):
- GitHub username / org name.
- Desired tier or number of additional reviews.
- Reason for needing more.

---

## Email Configuration

| Variable               | Example Value                                |
|------------------------|----------------------------------------------|
| `RESEND_API_KEY`       | `re_xxxxxxxxxxxx`                            |
| `EMAIL_FROM`           | `CodeSecAudit <noreply@codesecaudit.ai>`     |
| `OWNER_CONTACT_EMAIL`  | `omchoksi108@gmail.com`                      |

---

## Audit Trail

All sent emails are recorded in the `email_events` MongoDB collection for
deliverability monitoring:

| Field        | Description                    |
|--------------|--------------------------------|
| `to_email`   | Recipient address              |
| `template`   | Email template name            |
| `subject`    | Subject line                   |
| `resend_id`  | Resend API response ID         |
| `delivered`  | Success / failure              |
| `created_at` | Send timestamp                 |
