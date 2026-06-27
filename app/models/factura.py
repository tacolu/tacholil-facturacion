import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    serie_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("serie_facturacion.id"), nullable=False
    )
    numero: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    base_imponible: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cuota_iva: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="borrador")

    # UUID del cliente en tl-core — sin FK, sin constraint
    cliente_empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Datos del receptor snapshot al momento de emision
    receptor_nif: Mapped[str | None] = mapped_column(String(20), nullable=True)
    receptor_razon_social: Mapped[str | None] = mapped_column(String(200), nullable=True)
    receptor_direccion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    receptor_codigo_postal: Mapped[str | None] = mapped_column(String(10), nullable=True)
    receptor_municipio: Mapped[str | None] = mapped_column(String(100), nullable=True)
    receptor_provincia: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # VeriFactu hash-chain (se rellena al emitir)
    hash_registro: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hash_anterior: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    lineas: Mapped[list["FacturaLinea"]] = relationship(
        "FacturaLinea", back_populates="factura", cascade="all, delete-orphan",
        lazy="selectin",
    )


class FacturaLinea(Base):
    __tablename__ = "factura_lineas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    factura_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facturas.id"), nullable=False, index=True
    )
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    tipo_iva: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cuota_iva: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    factura: Mapped["Factura"] = relationship("Factura", back_populates="lineas")
