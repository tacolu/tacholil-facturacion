import uuid
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel


class EstadoFactura(str, Enum):
    BORRADOR = "borrador"
    EMITIDA = "emitida"
    PAGADA = "pagada"
    CANCELADA = "cancelada"


# --- Lineas ---

class LineaBase(BaseModel):
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    tipo_iva: Decimal


class LineaCreate(LineaBase):
    pass


class LineaRead(LineaBase):
    id: uuid.UUID
    subtotal: Decimal
    cuota_iva: Decimal

    model_config = {"from_attributes": True}


# --- Factura ---

class ReceptorIn(BaseModel):
    nif: str
    razon_social: str
    direccion: str
    codigo_postal: str | None = None
    municipio: str | None = None
    provincia: str | None = None


class FacturaCreate(BaseModel):
    serie_id: uuid.UUID
    fecha: date
    lineas: list[LineaCreate]
    cliente_empresa_id: uuid.UUID | None = None
    receptor: ReceptorIn | None = None


class FacturaRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    serie_id: uuid.UUID
    numero: str
    fecha: date
    base_imponible: Decimal
    cuota_iva: Decimal
    total: Decimal
    estado: EstadoFactura
    cliente_empresa_id: uuid.UUID | None = None
    receptor_nif: str | None = None
    receptor_razon_social: str | None = None
    receptor_direccion: str | None = None
    receptor_codigo_postal: str | None = None
    receptor_municipio: str | None = None
    receptor_provincia: str | None = None
    hash_registro: str | None = None
    hash_anterior: str | None = None
    lineas: list[LineaRead] = []

    model_config = {"from_attributes": True}


class FacturaListItem(BaseModel):
    id: uuid.UUID
    numero: str
    fecha: date
    total: Decimal
    estado: EstadoFactura
    receptor_razon_social: str | None = None

    model_config = {"from_attributes": True}
