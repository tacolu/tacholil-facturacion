from decimal import Decimal

import pytest

from app.services.impuestos import calcular_impuesto, calcular_linea


def test_iva_21():
    result = calcular_impuesto(Decimal("100.00"), "IVA21")
    assert result["cuota"] == Decimal("21.00")
    assert result["total"] == Decimal("121.00")


def test_igic_7():
    result = calcular_impuesto(Decimal("100.00"), "IGIC7")
    assert result["cuota"] == Decimal("7.00")


def test_tipo_invalido():
    with pytest.raises(ValueError, match="no reconocido"):
        calcular_impuesto(Decimal("100.00"), "FAKE")


def test_calcular_linea():
    result = calcular_linea(Decimal("2"), Decimal("50.00"), Decimal("21"))
    assert result["subtotal"] == Decimal("100.00")
    assert result["cuota_iva"] == Decimal("21.00")


def test_calcular_linea_redondeo():
    result = calcular_linea(Decimal("3"), Decimal("33.33"), Decimal("21"))
    assert result["subtotal"] == Decimal("99.99")
    assert result["cuota_iva"] == Decimal("21.00")
