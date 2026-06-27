import uuid
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emisor import DatosFiscalesEmisor
from app.models.serie import SerieFacturacion
from app.schemas.factura import EstadoFactura, FacturaCreate, LineaCreate, ReceptorIn
from app.services.factura_service import (
    anular_factura,
    crear_factura,
    emitir_factura,
    pagar_factura,
)


@pytest_asyncio.fixture
async def serie(db: AsyncSession, tenant_id: uuid.UUID):
    serie = SerieFacturacion(
        tenant_id=tenant_id,
        codigo="F",
        formato="{codigo}{ejercicio}-{numero:04d}",
        ejercicio=2026,
        ultimo_numero=0,
    )
    db.add(serie)
    await db.flush()
    return serie


@pytest_asyncio.fixture
async def emisor(db: AsyncSession, tenant_id: uuid.UUID):
    emisor = DatosFiscalesEmisor(
        tenant_id=tenant_id,
        nif="B42670240",
        razon_social="Tacografos Lucas SL",
        direccion="Calle Test 1, Madrid",
    )
    db.add(emisor)
    await db.flush()
    return emisor


def _factura_create(serie_id: uuid.UUID) -> FacturaCreate:
    return FacturaCreate(
        serie_id=serie_id,
        fecha=date(2026, 6, 27),
        lineas=[
            LineaCreate(
                descripcion="Revision tacografo",
                cantidad=Decimal("1"),
                precio_unitario=Decimal("100.00"),
                tipo_iva=Decimal("21"),
            ),
        ],
        receptor=ReceptorIn(
            nif="A12345678",
            razon_social="Transportes Test SL",
            direccion="Av. Prueba 2, Barcelona",
        ),
    )


@pytest.mark.asyncio
async def test_crear_factura(db, tenant_id, serie):
    data = _factura_create(serie.id)
    factura = await crear_factura(db, tenant_id, data)
    assert factura.estado == "borrador"
    assert factura.numero == "F2026-0001"
    assert factura.base_imponible == Decimal("100.00")
    assert factura.cuota_iva == Decimal("21.00")
    assert factura.total == Decimal("121.00")
    assert factura.receptor_nif == "A12345678"
    assert len(factura.lineas) == 1


@pytest.mark.asyncio
async def test_numeracion_secuencial(db, tenant_id, serie):
    for i in range(3):
        data = _factura_create(serie.id)
        factura = await crear_factura(db, tenant_id, data)
        assert factura.numero == f"F2026-{i+1:04d}"


@pytest.mark.asyncio
async def test_emitir_factura(db, tenant_id, serie, emisor):
    data = _factura_create(serie.id)
    factura = await crear_factura(db, tenant_id, data)
    emitida = await emitir_factura(db, factura.id, tenant_id)
    assert emitida.estado == "emitida"
    assert emitida.hash_registro is not None
    assert len(emitida.hash_registro) == 64


@pytest.mark.asyncio
async def test_pagar_factura(db, tenant_id, serie, emisor):
    data = _factura_create(serie.id)
    factura = await crear_factura(db, tenant_id, data)
    await emitir_factura(db, factura.id, tenant_id)
    pagada = await pagar_factura(db, factura.id, tenant_id)
    assert pagada.estado == "pagada"


@pytest.mark.asyncio
async def test_anular_desde_borrador(db, tenant_id, serie):
    data = _factura_create(serie.id)
    factura = await crear_factura(db, tenant_id, data)
    anulada = await anular_factura(db, factura.id, tenant_id)
    assert anulada.estado == "cancelada"


@pytest.mark.asyncio
async def test_transicion_invalida(db, tenant_id, serie):
    data = _factura_create(serie.id)
    factura = await crear_factura(db, tenant_id, data)
    with pytest.raises(ValueError, match="no permitida"):
        await pagar_factura(db, factura.id, tenant_id)


@pytest.mark.asyncio
async def test_pagada_no_anulable(db, tenant_id, serie, emisor):
    data = _factura_create(serie.id)
    factura = await crear_factura(db, tenant_id, data)
    await emitir_factura(db, factura.id, tenant_id)
    await pagar_factura(db, factura.id, tenant_id)
    with pytest.raises(ValueError, match="no permitida"):
        await anular_factura(db, factura.id, tenant_id)
