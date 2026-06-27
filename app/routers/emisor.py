import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.emisor import DatosFiscalesEmisor
from app.schemas.emisor import EmisorRead, EmisorUpdate

router = APIRouter(prefix="/emisor", tags=["emisor"])


async def get_tenant_id(x_tenant_id: uuid.UUID = Header(...)) -> uuid.UUID:
    return x_tenant_id


@router.get("/", response_model=EmisorRead)
async def get_emisor(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DatosFiscalesEmisor).where(DatosFiscalesEmisor.tenant_id == tenant_id)
    )
    emisor = result.scalar_one_or_none()
    if emisor is None:
        raise HTTPException(status_code=404, detail="Datos fiscales no configurados")
    return emisor


@router.put("/", response_model=EmisorRead)
async def update_emisor(
    data: EmisorUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DatosFiscalesEmisor).where(DatosFiscalesEmisor.tenant_id == tenant_id)
    )
    emisor = result.scalar_one_or_none()

    if emisor is None:
        # Crear si no existe — necesita al menos nif, razon_social, direccion
        if not data.nif or not data.razon_social or not data.direccion:
            raise HTTPException(
                status_code=400,
                detail="Primera vez: nif, razon_social y direccion son obligatorios",
            )
        emisor = DatosFiscalesEmisor(tenant_id=tenant_id)
        db.add(emisor)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(value, "value"):
            value = value.value
        setattr(emisor, field, value)

    await db.commit()
    await db.refresh(emisor)
    return emisor
