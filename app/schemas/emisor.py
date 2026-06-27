import uuid

from pydantic import BaseModel

from app.models.emisor import RegimenFiscal


class EmisorRead(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    nif: str
    razon_social: str
    nombre_comercial: str | None = None
    direccion: str
    codigo_postal: str | None = None
    municipio: str | None = None
    provincia: str | None = None
    regimen_fiscal: str

    model_config = {"from_attributes": True}


class EmisorUpdate(BaseModel):
    nif: str | None = None
    razon_social: str | None = None
    nombre_comercial: str | None = None
    direccion: str | None = None
    codigo_postal: str | None = None
    municipio: str | None = None
    provincia: str | None = None
    regimen_fiscal: RegimenFiscal | None = None
