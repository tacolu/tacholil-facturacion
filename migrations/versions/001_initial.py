"""Initial schema — facturas, series, emisor, verifactu

Revision ID: 001
Revises:
Create Date: 2026-06-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "datos_fiscales_emisor",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("nif", sa.String(20), nullable=False),
        sa.Column("razon_social", sa.String(200), nullable=False),
        sa.Column("nombre_comercial", sa.String(200), nullable=True),
        sa.Column("direccion", sa.String(500), nullable=False),
        sa.Column("codigo_postal", sa.String(10), nullable=True),
        sa.Column("municipio", sa.String(100), nullable=True),
        sa.Column("provincia", sa.String(100), nullable=True),
        sa.Column("regimen_fiscal", sa.String(50), nullable=False, server_default="iva_general"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "serie_facturacion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("formato", sa.String(100), nullable=False),
        sa.Column("ultimo_numero", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ejercicio", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "codigo", "ejercicio", name="uq_serie_tenant_codigo_ejercicio"),
    )

    op.create_table(
        "facturas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("serie_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("serie_facturacion.id"), nullable=False),
        sa.Column("numero", sa.String(50), nullable=False),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("base_imponible", sa.Numeric(12, 2), nullable=False),
        sa.Column("cuota_iva", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("cliente_empresa_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("receptor_nif", sa.String(20), nullable=True),
        sa.Column("receptor_razon_social", sa.String(200), nullable=True),
        sa.Column("receptor_direccion", sa.String(500), nullable=True),
        sa.Column("receptor_codigo_postal", sa.String(10), nullable=True),
        sa.Column("receptor_municipio", sa.String(100), nullable=True),
        sa.Column("receptor_provincia", sa.String(100), nullable=True),
        sa.Column("hash_registro", sa.String(64), nullable=True),
        sa.Column("hash_anterior", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "factura_lineas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("factura_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facturas.id"), nullable=False, index=True),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 4), nullable=False),
        sa.Column("precio_unitario", sa.Numeric(12, 4), nullable=False),
        sa.Column("tipo_iva", sa.Numeric(5, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False),
        sa.Column("cuota_iva", sa.Numeric(12, 2), nullable=False),
    )

    op.create_table(
        "registro_verifactu",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("factura_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("facturas.id"), nullable=False, index=True),
        sa.Column("hash_registro", sa.String(64), nullable=False),
        sa.Column("hash_anterior", sa.String(64), nullable=True),
        sa.Column("nif_emisor", sa.String(20), nullable=False),
        sa.Column("numero_serie", sa.String(70), nullable=False),
        sa.Column("timestamp_registro", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("registro_verifactu")
    op.drop_table("factura_lineas")
    op.drop_table("facturas")
    op.drop_table("serie_facturacion")
    op.drop_table("datos_fiscales_emisor")
