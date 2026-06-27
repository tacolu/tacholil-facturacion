import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RegistroVeriFactu(Base):
    """Registro de la cadena VeriFactu (RD 1007/2023). Cada emision genera un registro
    encadenado con el hash SHA-256 del anterior."""

    __tablename__ = "registro_verifactu"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    factura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=False, index=True
    )
    hash_registro: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_anterior: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nif_emisor: Mapped[str] = mapped_column(String(20), nullable=False)
    numero_serie: Mapped[str] = mapped_column(String(70), nullable=False)
    timestamp_registro: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
