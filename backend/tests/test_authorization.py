import hashlib
import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.models import Evidence, User, UserRole
from app.security import get_current_user

main_module = importlib.import_module("app.main")
app = main_module.app


@pytest.fixture
def setup_api(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(main_module.settings, "storage_root", str(tmp_path))
    actors = {}

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: actors["user"]

    with TestingSession() as db:
        owner = User(email="owner@example.test", password_hash="not-used", role=UserRole.analyst)
        other = User(email="other@example.test", password_hash="not-used", role=UserRole.analyst)
        viewer = User(email="viewer@example.test", password_hash="not-used", role=UserRole.viewer)
        db.add_all([owner, other, viewer])
        db.commit()
        db.refresh(owner)
        db.refresh(other)
        db.refresh(viewer)

        payload = b"synthetic evidence fixture"
        evidence = Evidence(
            case_reference="TEST-CASE-001",
            filename="synthetic.txt",
            media_type="text/plain",
            byte_size=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            storage_key="owner-evidence",
            uploaded_by=owner.id,
        )
        other_evidence = Evidence(
            case_reference="TEST-CASE-002",
            filename="other.txt",
            media_type="text/plain",
            byte_size=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
            storage_key="other-evidence",
            uploaded_by=other.id,
        )
        db.add_all([evidence, other_evidence])
        db.commit()
        db.refresh(evidence)
        db.refresh(other_evidence)
        (tmp_path / evidence.storage_key).write_bytes(payload)
        (tmp_path / other_evidence.storage_key).write_bytes(payload)

        actors.update(
            owner=owner,
            other=other,
            viewer=viewer,
            evidence=evidence,
            other_evidence=other_evidence,
        )

    client = TestClient(app)
    try:
        yield client, actors
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_evidence_list_only_returns_records_owned_by_current_user(setup_api):
    client, actors = setup_api
    actors["user"] = actors["owner"]

    response = client.get("/api/v1/evidence")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [actors["evidence"].id]


@pytest.mark.parametrize(
    ("method", "path_suffix"),
    [
        ("get", ""),
        ("post", "/verify"),
        ("post", "/anchor"),
        ("get", "/certificate"),
    ],
)
def test_user_cannot_access_another_users_evidence(setup_api, method, path_suffix):
    client, actors = setup_api
    actors["user"] = actors["owner"]
    evidence_id = actors["other_evidence"].id

    response = getattr(client, method)(f"/api/v1/evidence/{evidence_id}{path_suffix}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Evidence not found"


def test_viewer_cannot_upload_evidence(setup_api):
    client, actors = setup_api
    actors["user"] = actors["viewer"]

    response = client.post(
        "/api/v1/evidence",
        data={"case_reference": "TEST-CASE-VIEWER"},
        files={"file": ("sample.txt", b"synthetic", "text/plain")},
    )

    assert response.status_code == 403
    assert "Read-only role" in response.json()["detail"]


def test_viewer_cannot_request_certificate(setup_api):
    client, actors = setup_api
    actors["user"] = actors["viewer"]

    response = client.get(f"/api/v1/evidence/{actors['evidence'].id}/certificate")

    assert response.status_code == 403
