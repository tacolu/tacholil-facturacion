import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional


def _fmt(value) -> str:
    d = value if isinstance(value, Decimal) else Decimal(str(value))
    return str(d.quantize(Decimal("0.01")))


def _fecha_str(fecha) -> str:
    if hasattr(fecha, "strftime"):
        return fecha.strftime("%Y-%m-%d")
    return str(fecha)


def compute_record_hash(prev_hash: Optional[str], factura: dict) -> str:
    """Calcula SHA-256 del registro VeriFactu encadenado con la firma anterior.

    prev_hash=None o '' representa el primer registro de la cadena (sin predecesor).
    Devuelve hexdigest en MAYUSCULAS (64 chars).
    """
    effective_prev = prev_hash if prev_hash is not None else ""

    timestamp = factura.get("timestamp_registro") or datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    payload = "|".join([
        str(factura.get("nif_emisor", "")),
        f"{factura.get('serie', '')}{factura.get('numero', '')}",
        _fecha_str(factura.get("fecha_expedicion", "")),
        str(factura.get("tipo", "")),
        _fmt(factura.get("cuota_total", 0)),
        _fmt(factura.get("importe_total", 0)),
        effective_prev,
        str(timestamp),
    ])

    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()


def build_chained_record(prev_hash: Optional[str], factura: dict) -> dict:
    """Construye el dict del registro VeriFactu con hash encadenado."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    factura_ts = {**factura, "timestamp_registro": timestamp}

    hash_registro = compute_record_hash(prev_hash, factura_ts)

    return {
        "hash_anterior": prev_hash if prev_hash else None,
        "hash_registro": hash_registro,
        "nif_emisor": factura.get("nif_emisor"),
        "numero_serie": f"{factura.get('serie', '')}{factura.get('numero', '')}",
        "fecha_expedicion": factura.get("fecha_expedicion"),
        "cuota_total": factura.get("cuota_total"),
        "importe_total": factura.get("importe_total"),
        "timestamp_registro": timestamp,
    }
