import uuid
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.factura import Factura
from app.schemas.factura import (
    EstadoFactura,
    FacturaCreate,
    FacturaListItem,
    FacturaRead,
)
from app.services.factura_service import (
    anular_factura,
    crear_factura,
    emitir_factura,
    pagar_factura,
)

router = APIRouter(prefix="/facturas", tags=["facturas"])


async def get_tenant_id(x_tenant_id: uuid.UUID = Header(...)) -> uuid.UUID:
    return x_tenant_id


@router.post("/", response_model=FacturaRead, status_code=201)
async def create(
    data: FacturaCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        factura = await crear_factura(db, tenant_id, data)
        await db.commit()
        await db.refresh(factura)
        return factura
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/", response_model=list[FacturaListItem])
async def list_facturas(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    estado: EstadoFactura | None = None,
    cliente_id: uuid.UUID | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Factura).where(Factura.tenant_id == tenant_id)
    if estado is not None:
        stmt = stmt.where(Factura.estado == estado.value)
    if cliente_id is not None:
        stmt = stmt.where(Factura.cliente_empresa_id == cliente_id)
    if fecha_desde is not None:
        stmt = stmt.where(Factura.fecha >= fecha_desde)
    if fecha_hasta is not None:
        stmt = stmt.where(Factura.fecha <= fecha_hasta)
    stmt = stmt.order_by(Factura.fecha.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{factura_id}", response_model=FacturaRead)
async def get_factura(
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Factura).where(Factura.id == factura_id, Factura.tenant_id == tenant_id)
    )
    factura = result.scalar_one_or_none()
    if factura is None:
        raise HTTPException(status_code=404)
    return factura


@router.post("/{factura_id}/emitir", response_model=FacturaRead)
async def emitir(
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        factura = await emitir_factura(db, factura_id, tenant_id)
        await db.commit()
        await db.refresh(factura)
        return factura
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{factura_id}/pagar", response_model=FacturaRead)
async def pagar(
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        factura = await pagar_factura(db, factura_id, tenant_id)
        await db.commit()
        await db.refresh(factura)
        return factura
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{factura_id}/anular", response_model=FacturaRead)
async def anular(
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    try:
        factura = await anular_factura(db, factura_id, tenant_id)
        await db.commit()
        await db.refresh(factura)
        return factura
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{factura_id}/pdf")
async def get_pdf(
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    from fastapi.responses import Response

    from app.models.emisor import DatosFiscalesEmisor
    from app.services.pdf import EmisorPDF, FacturaPDFData, ReceptorPDF, render_factura_pdf

    result = await db.execute(
        select(Factura).where(Factura.id == factura_id, Factura.tenant_id == tenant_id)
    )
    factura = result.scalar_one_or_none()
    if factura is None:
        raise HTTPException(status_code=404)
    if factura.estado == EstadoFactura.BORRADOR.value:
        raise HTTPException(status_code=409, detail="No se genera PDF en estado borrador")

    # Cargar emisor
    emisor_result = await db.execute(
        select(DatosFiscalesEmisor).where(DatosFiscalesEmisor.tenant_id == tenant_id)
    )
    emisor_row = emisor_result.scalar_one_or_none()
    if emisor_row is None:
        raise HTTPException(status_code=400, detail="Datos fiscales del emisor no configurados")

    emisor = EmisorPDF(
        nif=emisor_row.nif,
        razon_social=emisor_row.razon_social,
        nombre_comercial=emisor_row.nombre_comercial,
        direccion=emisor_row.direccion,
        codigo_postal=emisor_row.codigo_postal,
        municipio=emisor_row.municipio,
        provincia=emisor_row.provincia,
        regimen_fiscal=emisor_row.regimen_fiscal,
    )

    receptor = None
    if factura.receptor_nif:
        receptor = ReceptorPDF(
            nif=factura.receptor_nif,
            razon_social=factura.receptor_razon_social or "",
            direccion=factura.receptor_direccion or "",
            codigo_postal=factura.receptor_codigo_postal,
            municipio=factura.receptor_municipio,
            provincia=factura.receptor_provincia,
        )

    # Convertir ORM -> schema para el PDF
    from app.schemas.factura import FacturaRead as FR
    factura_schema = FR.model_validate(factura)

    pdf_data = FacturaPDFData(factura=factura_schema, emisor=emisor, receptor=receptor)
    pdf_bytes = render_factura_pdf(pdf_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="factura-{factura.numero}.pdf"'},
    )
