import pytest
from fastapi import HTTPException
from app.models.users import User, UserRole
from app.auth.rbac import require_roles
from app.auth.jwt import create_access_token, decode_access_token

def test_jwt_create_and_decode():
    data = {"user_id": 99, "email": "test@domain.com", "role": "ADMIN"}
    token = create_access_token(data)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["user_id"] == 99
    assert payload["email"] == "test@domain.com"
    assert payload["role"] == "ADMIN"

def test_jwt_invalid_token():
    payload = decode_access_token("invalid.jwt.token")
    assert payload is None

def test_require_roles_success():
    admin_user = User(id=1, email="admin@system.com", role=UserRole.ADMIN, is_active=True)
    checker = require_roles([UserRole.ADMIN, UserRole.SITE_MANAGER])
    result = checker(current_user=admin_user)
    assert result.id == 1
    assert result.role == UserRole.ADMIN

def test_require_roles_forbidden():
    auditor_user = User(id=2, email="auditor@system.com", role=UserRole.AUDITOR, is_active=True)
    checker = require_roles([UserRole.ADMIN, UserRole.OPERATOR])
    
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=auditor_user)
    assert exc_info.value.status_code == 403
    assert "does not have permission" in exc_info.value.detail

def test_password_hashing_and_verification():
    from app.auth.passwords import get_password_hash, verify_password
    pw_hash = get_password_hash("password123")
    assert isinstance(pw_hash, str)
    assert len(pw_hash) == 64
    assert verify_password("password123", pw_hash) is True
    assert verify_password("wrongpassword", pw_hash) is False
    assert verify_password("", pw_hash) is False
    assert verify_password("password123", "") is False

@pytest.fixture
def auth_client():
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.orm import sessionmaker
    from app.main import app as fastapi_app
    from app.database import Base, get_db
    from app.auth.passwords import get_password_hash
    import app.models

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()

    # Seed an active test operator and an inactive test user
    hashed = get_password_hash("password123")
    active_user = User(
        email="operator@sitea.com",
        password_hash=hashed,
        full_name="Alex Operator",
        role=UserRole.OPERATOR,
        is_active=True
    )
    inactive_user = User(
        email="inactive@sitea.com",
        password_hash=hashed,
        full_name="Inactive User",
        role=UserRole.OPERATOR,
        is_active=False
    )
    session.add_all([active_user, inactive_user])
    session.commit()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client
    fastapi_app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_login_success_and_case_insensitivity(auth_client):
    # Standard lowercase login
    res = auth_client.post("/api/v1/auth/login", json={"email": "operator@sitea.com", "password": "password123"})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "Operator"
    assert "access_token" in body

    # Case-insensitive and trimmed email
    res2 = auth_client.post("/api/v1/auth/login", json={"email": "  OPERATOR@SITEA.COM  ", "password": "password123"})
    assert res2.status_code == 200
    assert res2.json()["role"] == "Operator"

def test_login_invalid_password(auth_client):
    res = auth_client.post("/api/v1/auth/login", json={"email": "operator@sitea.com", "password": "wrongpassword"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"

def test_login_nonexistent_user(auth_client):
    res = auth_client.post("/api/v1/auth/login", json={"email": "nonexistent@sitea.com", "password": "password123"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"

def test_login_deactivated_account(auth_client):
    res = auth_client.post("/api/v1/auth/login", json={"email": "inactive@sitea.com", "password": "password123"})
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"]

def test_cors_options_preflight(auth_client):
    # Production Vercel domain preflight
    res = auth_client.options("/api/v1/auth/login", headers={
        "Origin": "https://smart-vehicle-compliance-platform.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    })
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://smart-vehicle-compliance-platform.vercel.app"

    # Preview Vercel domain preflight regex
    res_preview = auth_client.options("/api/v1/auth/login", headers={
        "Origin": "https://smart-vehicle-preview-abc.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    })
    assert res_preview.status_code == 200
    assert res_preview.headers.get("access-control-allow-origin") == "https://smart-vehicle-preview-abc.vercel.app"

