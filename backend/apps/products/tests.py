import pytest
from decimal import Decimal


class TestProductModel:
    def test_create_product(self, product):
        assert product.id is not None
        assert product.name == "Test Produkt"

    def test_product_str(self, product):
        assert str(product) == "ART-001 - Test Produkt"

    def test_product_price(self, product):
        assert product.unit_price == Decimal("100.00")
        assert product.vat_rate == Decimal("19.00")


class TestProductAPI:
    def test_list_products(self, api_client, product):
        response = api_client.get("/api/products/")
        assert response.status_code == 200
        assert response.data["count"] == 1

    def test_get_product(self, api_client, product):
        response = api_client.get(f"/api/products/{product.id}/")
        assert response.status_code == 200
        assert response.data["name"] == "Test Produkt"

    def test_create_product(self, api_client, tenant):
        data = {
            "sku": "ART-002",
            "name": "Neues Produkt",
            "unit_price": "200.00",
            "vat_rate": "19.00",
        }
        response = api_client.post("/api/products/", data)
        assert response.status_code == 201
        assert response.data["name"] == "Neues Produkt"

    def test_update_product(self, api_client, product):
        data = {"name": "Geändertes Produkt"}
        response = api_client.patch(f"/api/products/{product.id}/", data)
        assert response.status_code == 200
        assert response.data["name"] == "Geändertes Produkt"

    def test_delete_product(self, api_client, product):
        response = api_client.delete(f"/api/products/{product.id}/")
        assert response.status_code == 204
