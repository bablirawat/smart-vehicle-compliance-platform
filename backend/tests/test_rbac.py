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
