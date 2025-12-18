import pytest
from decimal import Decimal


class TestCustomerModel:
    def test_create_customer(self, customer):
        assert customer.id is not None
        assert customer.company_name == "Kunde GmbH"

    def test_customer_str(self, customer):
        assert str(customer) == "Kunde GmbH"

    def test_display_name(self, customer):
        assert customer.display_name == "Kunde GmbH"


class TestCustomerAPI:
    def test_list_customers(self, api_client, customer):
        response = api_client.get("/api/customers/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_get_customer(self, api_client, customer):
        response = api_client.get(f"/api/customers/{customer.id}/")
        assert response.status_code == 200
        assert response.data["company_name"] == "Kunde GmbH"

    def test_create_customer(self, api_client, tenant):
        data = {
            "customer_number": "K-002",
            "company_name": "Neue Firma GmbH",
            "street": "Neue Str. 1",
            "zip_code": "54321",
            "city": "Hamburg",
            "country": "DE",
            "email": "neu@example.com",
        }
        response = api_client.post("/api/customers/", data)
        assert response.status_code == 201
        assert response.data["company_name"] == "Neue Firma GmbH"

    def test_update_customer(self, api_client, customer):
        data = {"company_name": "Geänderte GmbH"}
        response = api_client.patch(f"/api/customers/{customer.id}/", data)
        assert response.status_code == 200
        assert response.data["company_name"] == "Geänderte GmbH"

    def test_delete_customer(self, api_client, customer):
        response = api_client.delete(f"/api/customers/{customer.id}/")
        assert response.status_code == 204