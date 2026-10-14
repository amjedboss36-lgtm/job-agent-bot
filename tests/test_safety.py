import sqlite3

import queue_manager
from apply_extractor import is_trusted_domain


def test_trusted_domains_match_exact_hosts_and_subdomains():
    assert is_trusted_domain("https://jobs.lever.co/example")
    assert is_trusted_domain("https://careers.indeed.com/nurse")


def test_trusted_domain_rejects_lookalike_and_unsafe_urls():
    assert not is_trusted_domain("https://indeed.com.attacker.example/jobs")
    assert not is_trusted_domain("https://fakelever.co/jobs")
    assert not is_trusted_domain("javascript://indeed.com")
    assert not is_trusted_domain("https://facebook.com/jobs")


def test_add_job_generates_stable_id_and_rejects_duplicate(tmp_path, monkeypatch):
    db_path = tmp_path / "test_jobs.db"
    monkeypatch.setattr(queue_manager, "DB_FILE", str(db_path))
    queue_manager.init_db()

    job = {
        "title": "Registered Nurse",
        "link": "https://example.org/jobs/123#details",
        "country": "Germany",
        "description": "Nursing role",
        "source": "Test",
        "score": 75,
        "priority_flags": ["nursing", "relocation"],
    }
    assert queue_manager.add_job(job) is True
    assert queue_manager.add_job(job) is False

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT id, priority_flags FROM jobs").fetchall()

    assert len(rows) == 1
    assert rows[0][0]
    assert rows[0][1] == "nursing,relocation"


def test_add_job_rejects_missing_title_or_non_http_link(tmp_path, monkeypatch):
    monkeypatch.setattr(queue_manager, "DB_FILE", str(tmp_path / "test_jobs.db"))
    queue_manager.init_db()

    assert not queue_manager.add_job({"title": "", "link": "https://example.org"})
    assert not queue_manager.add_job({"title": "Nurse", "link": "javascript:alert(1)"})



def test_admin_endpoints_are_closed_without_configured_key(tmp_path, monkeypatch):
    import app as application
    monkeypatch.setattr(queue_manager, "DB_FILE", str(tmp_path / "api_test.db"))
    queue_manager.init_db()
    client = application.app.test_client()

    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    assert client.post("/scrape").status_code == 503

    monkeypatch.setenv("ADMIN_API_KEY", "unit-test-secret")
    assert client.post("/scrape", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert client.get("/stats", headers={"X-Admin-Key": "unit-test-secret"}).status_code == 200
    assert client.get("/applications", headers={"X-Admin-Key": "unit-test-secret"}).status_code == 200



def test_automatic_email_requires_cv_attachment(tmp_path, monkeypatch):
    import telegram_bot

    monkeypatch.setattr(telegram_bot, "SMTP_EMAIL", "sender@example.org")
    monkeypatch.setattr(telegram_bot, "SMTP_PASSWORD", "test-only")
    monkeypatch.delenv("CV_FILE_PATH", raising=False)
    assert telegram_bot.send_email_application(
        "hr@example.org", "Nurse", "Cover letter"
    ) is False


def test_automatic_email_attaches_configured_cv(tmp_path, monkeypatch):
    import email
    import telegram_bot

    cv = tmp_path / "candidate.pdf"
    cv.write_bytes(b"%PDF-1.4 test CV")
    monkeypatch.setattr(telegram_bot, "SMTP_EMAIL", "sender@example.org")
    monkeypatch.setattr(telegram_bot, "SMTP_PASSWORD", "test-only")
    monkeypatch.setattr(telegram_bot, "SMTP_SERVER", "smtp.example.org")
    monkeypatch.setattr(telegram_bot, "SMTP_PORT", 587)
    monkeypatch.setenv("CV_FILE_PATH", str(cv))

    captured = {}

    class FakeSMTP:
        def __init__(self, server, port):
            captured["server"] = server
            captured["port"] = port

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            pass

        def login(self, sender, password):
            captured["sender"] = sender

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(telegram_bot.smtplib, "SMTP", FakeSMTP)
    assert telegram_bot.send_email_application(
        "hr@example.org", "Nurse", "Cover letter"
    ) is True
    message = captured["message"]
    attachments = [part for part in message.walk() if part.get_content_disposition() == "attachment"]
    assert len(attachments) == 1
    assert attachments[0].get_filename() == "candidate.pdf"



def test_job_link_validation_rejects_lookalikes_and_accepts_https():
    from filters import is_valid_job_link

    assert is_valid_job_link("https://jobs.example.com/vacancy/1")
    assert not is_valid_job_link("javascript:alert(1)")
    assert not is_valid_job_link("https://eures.europa.eu.evil.example/jobs")
    assert not is_valid_job_link("https://user:pass@jobs.example.com/apply")


def test_scraper_integrates_public_api_jobs_and_deduplicates(monkeypatch):
    import scraper

    monkeypatch.setattr(scraper, "collect_all_jobs", lambda: [
        {"title": "Nurse", "link": "https://example.org/job/1", "country": "Yemen", "description": "nursing", "source": "API"},
        {"title": "Duplicate", "link": "https://example.org/job/1", "country": "Yemen", "description": "nursing", "source": "Other"},
        {"title": "Bad URL", "link": "javascript:bad()", "country": "Unknown", "description": "", "source": "API"},
    ])
    monkeypatch.setattr(scraper, "scrape_indeed", lambda: [])
    monkeypatch.setattr(scraper, "scrape_linkedin", lambda: [])
    monkeypatch.setattr(scraper, "scrape_greenhouse", lambda: [])

    jobs = scraper.scrape_jobs()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Nurse"



def test_general_job_categories_receive_relevance_points():
    from scoring import calculate_score

    result = calculate_score({
        "title": "Customer Service Representative",
        "description": "Customer service job with training provided",
        "country": "Canada",
    })
    assert result["score"] >= 30
    assert "GENERAL_ROLE" in result["priority_flags"] or "ADMIN_ROLE" in result["priority_flags"]



def test_process_never_sends_without_per_job_approval(tmp_path, monkeypatch):
    import app as application
    from queue_manager import add_job, init_db, ApplicationMode

    monkeypatch.setattr(queue_manager, "DB_FILE", str(tmp_path / "approval_test.db"))
    init_db()
    assert add_job({
        "id": "approval-test-1",
        "title": "Registered Nurse",
        "link": "https://jobs.example.org/1",
        "country": "Canada",
        "description": "Apply via hr@example.org",
        "source": "Test",
        "score": 80,
    })
    monkeypatch.setenv("ADMIN_API_KEY", "unit-test-secret")
    monkeypatch.setenv("AUTO_APPLY_ENABLED", "true")
    monkeypatch.setattr(application, "decide_application_mode", lambda job, score: {
        "mode": ApplicationMode.AUTO_APPLY,
        "apply_email": "hr@example.org",
        "apply_url": None,
        "confidence_score": 0.95,
        "reasoning": "test",
    })
    sent = {"called": False}

    def fake_send(*args, **kwargs):
        sent["called"] = True
        return True

    monkeypatch.setattr(application, "send_email_application", fake_send)
    monkeypatch.setattr(application, "notify_job_sent", lambda *args, **kwargs: True)
    monkeypatch.setattr(application, "notify_summary", lambda *args, **kwargs: True)

    client = application.app.test_client()
    response = client.post("/process", headers={"X-Admin-Key": "unit-test-secret"})
    assert response.status_code == 200
    assert sent["called"] is False
    item = queue_manager.get_recent_jobs(limit=10)[0]
    assert item["status"] == "queued"



def test_google_web_jobs_uses_configured_google_cse_and_deduplicates(monkeypatch):
    import sources

    monkeypatch.setenv("GOOGLE_CSE_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_CSE_CX", "test-engine")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"items": [{
                "title": "Registered Nurse - Official Careers",
                "link": "https://hospital.example/jobs/nurse",
                "snippet": "Apply through the official employer careers page",
                "displayLink": "hospital.example",
            }]}

    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(params["q"])
        return FakeResponse()

    monkeypatch.setattr(sources.requests, "get", fake_get)
    jobs = sources.google_web_jobs()
    assert len(jobs) == 1
    assert jobs[0]["link"] == "https://hospital.example/jobs/nurse"
    assert jobs[0]["source"] == "Google Web Search"
    assert len(calls) == 8


def test_google_web_jobs_skips_cleanly_without_credentials(monkeypatch):
    import sources

    monkeypatch.delenv("GOOGLE_CSE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_CX", raising=False)
    assert sources.google_web_jobs() == []



def test_brave_web_jobs_uses_token_and_deduplicates(monkeypatch):
    import sources

    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-brave-key")

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"web": {"results": [{
                "title": "Registered Nurse - Official Careers",
                "url": "https://hospital.example/jobs/nurse",
                "description": "Apply through the official employer careers page",
            }]}}

    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        assert url == "https://api.search.brave.com/res/v1/web/search"
        assert headers["X-Subscription-Token"] == "test-brave-key"
        calls.append(params["q"])
        return FakeResponse()

    monkeypatch.setattr(sources.requests, "get", fake_get)
    jobs = sources.brave_web_jobs()
    assert len(jobs) == 1
    assert jobs[0]["link"] == "https://hospital.example/jobs/nurse"
    assert jobs[0]["source"] == "Brave Web Search"
    assert len(calls) == 8


def test_brave_web_jobs_skips_without_token(monkeypatch):
    import sources

    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    assert sources.brave_web_jobs() == []
