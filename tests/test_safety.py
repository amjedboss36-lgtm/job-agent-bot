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
