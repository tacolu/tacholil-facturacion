import uuid
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.emisor import DatosFiscalesEmisor
from app.models.factura import Factura, FacturaLinea
from app.models.registro_verifactu import RegistroVeriFactu
from app.schemas.factura import EstadoFactura, FacturaCreate
from app.services.impuestos import calcular_linea
from app.services.numeracion import siguiente_numero
from app.services.verifactu import build_chained_record

# Transiciones validas de estado
_TRANSICIONES = {
    EstadoFactura.BORRADOR: {EstadoFactura.EMITIDA, EstadoFactura.CANCELADA},
    EstadoFactura.EMITIDA: {EstadoFactura.PAGADA, EstadoFactura.CANCELADA},
    EstadoFactura.PAGADA: set(),
    EstadoFactura.CANCELADA: set(),
}


async def crear_factura(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    data: FacturaCreate,
) -> Factura:
    """Crea factura en estado borrador con numeracion legal automatica."""
    numero = await siguiente_numero(db, data.serie_id)

    total_base = Decimal("0")
    total_cuota = Decimal("0")
    lineas_orm = []

    for linea_in in data.lineas:
        calc = calcular_linea(linea_in.cantidad, linea_in.precio_unitario, linea_in.tipo_iva)
        total_base += calc["subtotal"]
        total_cuota += calc["cuota_iva"]
        lineas_orm.append(FacturaLinea(
            descripcion=linea_in.descripcion,
            cantidad=linea_in.cantidad,
            precio_unitario=linea_in.precio_unitario,
            tipo_iva=linea_in.tipo_iva,
            subtotal=calc["subtotal"],
            cuota_iva=calc["cuota_iva"],
        ))

    factura = Factura(
        tenant_id=tenant_id,
        serie_id=data.serie_id,
        numero=numero,
        fecha=data.fecha,
        base_imponible=total_base,
        cuota_iva=total_cuota,
        total=total_base + total_cuota,
        estado=EstadoFactura.BORRADOR.value,
        cliente_empresa_id=data.cliente_empresa_id,
    )

    if data.receptor:
        factura.receptor_nif = data.receptor.nif
        factura.receptor_razon_social = data.receptor.razon_social
        factura.receptor_direccion = data.receptor.direccion
        factura.receptor_codigo_postal = data.receptor.codigo_postal
        factura.receptor_municipio = data.receptor.municipio
        factura.receptor_provincia = data.receptor.provincia

    factura.lineas = lineas_orm
    db.add(factura)
    await db.flush()
    return factura


def _validar_transicion(actual: str, nuevo: EstadoFactura) -> None:
    actual_enum = EstadoFactura(actual)
    permitidos = _TRANSICIONES.get(actual_enum, set())
    if nuevo not in permitidos:
        raise ValueError(
            f"Transicion {actual} -> {nuevo.value} no permitida. "
            f"Permitidos: {[e.value for e in permitidos]}"
        )


async def emitir_factura(
    db: AsyncSession,
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Factura:
    """Transiciona factura borrador -> emitida, genera hash VeriFactu."""
    factura = await _get_factura(db, factura_id, tenant_id)
    _validar_transicion(factura.estado, EstadoFactura.EMITIDA)

    # Obtener emisor para VeriFactu
    emisor_result = await db.execute(
        select(DatosFiscalesEmisor).where(DatosFiscalesEmisor.tenant_id == tenant_id)
    )
    emisor = emisor_result.scalar_one_or_none()
    nif_emisor = emisor.nif if emisor else ""

    # Obtener hash anterior (ultimo registro VeriFactu del tenant)
    prev_result = await db.execute(
        select(RegistroVeriFactu.hash_registro)
        .where(RegistroVeriFactu.tenant_id == tenant_id)
        .order_by(RegistroVeriFactu.created_at.desc())
        .limit(1)
    )
    prev_hash = prev_result.scalar_one_or_none()

    # Construir registro VeriFactu
    serie_result = await db.execute(
        select(SerieFacturacion.codigo).where(SerieFacturacion.id == factura.serie_id)
    )
    serie_codigo = serie_result.scalar_one_or_none() or ""

    record = build_chained_record(prev_hash, {
        "nif_emisor": nif_emisor,
        "serie": serie_codigo,
        "numero": factura.numero,
        "fecha_expedicion": factura.fecha,
        "tipo": "F1",
        "cuota_total": factura.cuota_iva,
        "importe_total": factura.total,
    })

    # Persistir registro VeriFactu
    reg = RegistroVeriFactu(
        tenant_id=tenant_id,
        factura_id=factura_id,
        hash_registro=record["hash_registro"],
        hash_anterior=record["hash_anterior"],
        nif_emisor=nif_emisor,
        numero_serie=record["numero_serie"],
        timestamp_registro=record["timestamp_registro"],
    )
    db.add(reg)

    # Actualizar factura
    factura.estado = EstadoFactura.EMITIDA.value
    factura.hash_registro = record["hash_registro"]
    factura.hash_anterior = record["hash_anterior"]

    await db.flush()
    return factura


async def pagar_factura(
    db: AsyncSession,
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Factura:
    factura = await _get_factura(db, factura_id, tenant_id)
    _validar_transicion(factura.estado, EstadoFactura.PAGADA)
    factura.estado = EstadoFactura.PAGADA.value
    await db.flush()
    return factura


async def anular_factura(
    db: AsyncSession,
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Factura:
    factura = await _get_factura(db, factura_id, tenant_id)
    _validar_transicion(factura.estado, EstadoFactura.CANCELADA)
    factura.estado = EstadoFactura.CANCELADA.value
    await db.flush()
    return factura


async def _get_factura(
    db: AsyncSession,
    factura_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Factura:
    result = await db.execute(
        select(Factura).where(Factura.id == factura_id, Factura.tenant_id == tenant_id)
    )
    factura = result.scalar_one_or_none()
    if factura is None:
        raise ValueError(f"Factura {factura_id} no encontrada para tenant {tenant_id}")
    return factura


# Import necesario para emitir_factura
from app.models.serie import SerieFacturacion  # noqa: E402
