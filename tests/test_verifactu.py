from decimal import Decimal

from app.services.verifactu import build_chained_record, compute_record_hash


def _factura_dict(**overrides):
    base = {
        "nif_emisor": "B42670240",
        "serie": "F",
        "numero": "F2026-0001",
        "fecha_expedicion": "2026-06-27",
        "tipo": "F1",
        "cuota_total": Decimal("21.00"),
        "importe_total": Decimal("121.00"),
        "timestamp_registro": "2026-06-27T12:00:00Z",
    }
    base.update(overrides)
    return base


def test_hash_determinista():
    factura = _factura_dict()
    h1 = compute_record_hash(None, factura)
    h2 = compute_record_hash(None, factura)
    assert h1 == h2
    assert len(h1) == 64
    assert h1 == h1.upper()


def test_hash_encadenado_diferente():
    factura = _factura_dict()
    h1 = compute_record_hash(None, factura)
    h2 = compute_record_hash(h1, factura)
    assert h1 != h2


def test_build_chained_first():
    factura = _factura_dict()
    record = build_chained_record(None, factura)
    assert record["hash_anterior"] is None
    assert len(record["hash_registro"]) == 64
    assert record["nif_emisor"] == "B42670240"


def test_build_chained_second():
    factura = _factura_dict()
    r1 = build_chained_record(None, factura)
    r2 = build_chained_record(r1["hash_registro"], factura)
    assert r2["hash_anterior"] == r1["hash_registro"]
    assert r2["hash_registro"] != r1["hash_registro"]


def test_cadena_sin_rotura():
    """Verifica que 5 registros encadenados mantienen integridad."""
    prev_hash = None
    hashes = []
    for i in range(5):
        factura = _factura_dict(
            numero=f"F2026-{i+1:04d}",
            timestamp_registro=f"2026-06-27T12:{i:02d}:00Z",
        )
        record = build_chained_record(prev_hash, factura)
        assert record["hash_anterior"] == (hashes[-1] if hashes else None)
        hashes.append(record["hash_registro"])
        prev_hash = record["hash_registro"]

    assert len(set(hashes)) == 5
