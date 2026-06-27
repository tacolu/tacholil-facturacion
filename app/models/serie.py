import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SerieFacturacion(Base):
    """Serie de numeracion para facturas. El contador ultimo_numero se incrementa
    atomicamente en el repositorio (SELECT FOR UPDATE) para garantizar sin huecos."""

    __tablename__ = "serie_facturacion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "codigo", "ejercicio",
            name="uq_serie_tenant_codigo_ejercicio",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    formato: Mapped[str] = mapped_column(String(100), nullable=False)
    ultimo_numero: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ejercicio: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
