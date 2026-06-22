# Usage Limits

## Free Tier

| Limit                          | Value     |
|--------------------------------|-----------|
| PR reviews per month           | 30        |
| Window                         | 30 days   |
| Max files per PR               | 30        |
| Max file size (KB)             | 200       |
| Max inline comments per PR     | 10        |
| RAG support                    | No        |
| RAG limit (future Pro tier)    | Unlimited |

---

## Enforcement

1. **Counter**: Each `pr_review` usage event increments the user's
   `reviews_used` counter for the current 30-day window.

2. **Check**: Before processing a PR review, the API checks
   `reviews_used < reviews_limit + extra_reviews`. If false:
   - Review is **blocked** (HTTP 429 or skipped webhook).
   - A `limit_reached` email is sent (see [email_workflows.md](email_workflows.md)).
   - The response/comment includes a link to contact the owner.

3. **Reset**: `window_start` is set on first usage event. After 30 days, a
   cron job (or on-next-request check) resets `reviews_used = 0` and
   `window_start = now`.

4. **Admin override**: `extra_reviews` field on the user document allows
   manual limit increases without changing plan definitions. Set via
   `ALLOW_MANUAL_LIMIT_INCREASE=true` and `DEFAULT_EXTRA_PR_LIMIT=20`.

---

## Dashboard Display

The Streamlit dashboard shows:

- Remaining reviews: `reviews_limit + extra_reviews - reviews_used`
- Days until reset: `(window_start + 30d) - now`
- Usage bar (green → yellow → red as limit approaches)

---

## Email Triggers

| Event                      | Trigger                                   | Action                           |
|----------------------------|-------------------------------------------|----------------------------------|
| Limit approaching (80%)    | `reviews_used >= reviews_limit * 0.8`     | Soft warning (future)            |
| Limit reached              | `reviews_used >= reviews_limit`           | Block review + send email        |
| Extra reviews granted      | `extra_reviews` increased by admin        | Confirmation email (future)      |

---

## Owner Contact

Users who hit the limit see a block message with a `mailto:omchoksi108@gmail.com`
link. The owner can manually increase the user's `extra_reviews` or upgrade them
to a custom tier.
