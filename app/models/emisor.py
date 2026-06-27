import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RegimenFiscal(str, Enum):
    IVA_GENERAL = "iva_general"
    IVA_SIMPLIFICADO = "iva_simplificado"
    IVA_RECARGO_EQUIVALENCIA = "iva_recargo_equivalencia"
    IGIC_GENERAL = "igic_general"
    IGIC_SIMPLIFICADO = "igic_simplificado"
    EXENTO = "exento"


class DatosFiscalesEmisor(Base):
    """Datos fiscales del emisor (empresa que emite facturas). Un registro por tenant."""

    __tablename__ = "datos_fiscales_emisor"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    nif: Mapped[str] = mapped_column(String(20), nullable=False)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    nombre_comercial: Mapped[str | None] = mapped_column(String(200), nullable=True)
    direccion: Mapped[str] = mapped_column(String(500), nullable=False)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    municipio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provincia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    regimen_fiscal: Mapped[str] = mapped_column(
        String(50), nullable=False, default=RegimenFiscal.IVA_GENERAL.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
