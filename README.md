# Job Agent Bot

This service discovers job postings, scores relevance, prepares cover letters, and sends Telegram alerts. It can email applications only when explicitly enabled; **automatic application sending is disabled by default**.

## Safety requirements
- Set `ADMIN_API_KEY` before using `/scrape`, `/process`, `/stats`, or `/applications`. The dashboard asks for this key when an action is run.
- Keep `AUTO_APPLY_ENABLED=false` until your candidate profile, CV attachment, target criteria, and recipient-verification policy are configured and tested.
- SMTP acceptance is not proof the employer received or reviewed an application.
- Never commit credentials or your CV to this repository.

## Environment variables
- `ADMIN_API_KEY`: long random secret required for protected API routes.
- `BOT_TOKEN`, `CHAT_ID`: Telegram bot and destination.
- `SMTP_EMAIL`, `SMTP_PASSWORD`, optional `SMTP_SERVER`, `SMTP_PORT`: outgoing mail.
- `OPENAI_API_KEY`, optional `OPENAI_MODEL`: cover-letter generation.
- `AUTO_APPLY_ENABLED`: defaults to `false`.
- `CV_FILE_PATH`: path to a candidate-owned PDF/DOC/DOCX file; required for automated email sending (maximum 10 MB). Do not store the CV in the Git repository.
- `USER_NAME`, `USER_SKILLS`, `USER_EXPERIENCE`: temporary profile values; replace with verified candidate details.
- `DB_FILE`: optional persistent SQLite path (must be on persistent storage if deployed).

## Tracking
- `GET /health`: public health check.
- `GET /stats`: queue count and daily send limit (requires `X-Admin-Key`).
- `GET /applications?limit=100`: recent jobs with status, source link, timestamps, and failure reason (requires `X-Admin-Key`).
- `POST /scrape`: discover and queue suitable jobs (requires `X-Admin-Key`).
- `POST /process`: process the queue (requires `X-Admin-Key`).

Statuses distinguish pending, queued for review, sent, failed, and skipped. A queued/guided/manual item is not an application submission.

## Local tests
```bash
python -m pip install -r requirements.txt pytest
pytest -q
```
