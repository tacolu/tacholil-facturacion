import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.serie import SerieFacturacion


async def siguiente_numero(db: AsyncSession, serie_id: uuid.UUID) -> str:
    """Obtiene el siguiente numero de factura para la serie dada.
    Usa SELECT FOR UPDATE para garantizar secuencialidad sin huecos."""
    stmt = (
        select(SerieFacturacion)
        .where(SerieFacturacion.id == serie_id)
        .with_for_update()
    )
    result = await db.execute(stmt)
    serie = result.scalar_one_or_none()
    if serie is None:
        raise ValueError(f"Serie {serie_id} no encontrada")

    serie.ultimo_numero += 1
    numero = serie.formato.format(
        codigo=serie.codigo,
        ejercicio=serie.ejercicio,
        numero=serie.ultimo_numero,
    )
    return numero
