from decimal import ROUND_HALF_UP, Decimal

TIPOS_IMPUESTO = {
    "IVA21": Decimal("21"),
    "IVA10": Decimal("10"),
    "IVA4": Decimal("4"),
    "IGIC7": Decimal("7"),
    "IGIC3": Decimal("3"),
    "EXENTO": Decimal("0"),
}


def calcular_impuesto(base: Decimal, tipo: str) -> dict:
    tipo_key = tipo.strip().upper()
    if tipo_key not in TIPOS_IMPUESTO:
        raise ValueError(f"Tipo de impuesto no reconocido: {tipo!r}")
    pct = TIPOS_IMPUESTO[tipo_key]
    cuota = (base * pct / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return {
        "base": base,
        "tipo_impositivo": pct,
        "cuota": cuota,
        "total": base + cuota,
    }


def calcular_linea(cantidad: Decimal, precio_unitario: Decimal, tipo_iva: Decimal) -> dict:
    """Calcula subtotal y cuota IVA de una linea de factura."""
    subtotal = (cantidad * precio_unitario).quantize(Decimal("0.01"), ROUND_HALF_UP)
    cuota = (subtotal * tipo_iva / Decimal("100")).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return {"subtotal": subtotal, "cuota_iva": cuota}
