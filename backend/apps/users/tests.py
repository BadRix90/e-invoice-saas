import pytest


class TestTenantModel:
    def test_create_tenant(self, tenant):
        assert tenant.id is not None
        assert tenant.name == "Test GmbH"

    def test_tenant_str(self, tenant):
        assert tenant.name == "Test GmbH"


class TestUserModel:
    def test_create_user(self, user):
        assert user.id is not None
        assert user.username == "testuser"
        assert user.tenant is not None

    def test_user_has_tenant(self, user, tenant):
        assert user.tenant == tenant


class TestAuthAPI:
    def test_login(self, client, user):
        response = client.post("/api/auth/token/", {
            "username": "testuser",
            "password": "testpass123",
        }, content_type="application/json")
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, client, user):
        response = client.post("/api/auth/token/", {
            "username": "testuser",
            "password": "wrongpassword",
        }, content_type="application/json")
        assert response.status_code == 401

    def test_protected_endpoint_without_token(self, client):
        response = client.get("/api/invoices/")
        assert response.status_code == 401

    def test_protected_endpoint_with_token(self, api_client):
        response = api_client.get("/api/invoices/")
        assert response.status_code == 200


class TestTenantAPI:
    def test_get_current_tenant(self, api_client, tenant):
        response = api_client.get("/api/tenants/current/")
        assert response.status_code == 200
        assert response.data["name"] == "Test GmbH"