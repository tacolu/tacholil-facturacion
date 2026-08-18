# tacholil-facturacion

Microservicio de facturación multi-tenant para Tacholil. FastAPI + PostgreSQL 16 + Alembic. Diseñado para integrarse con tl-minimo via API interna.

## Arquitectura

```
app/
  main.py              FastAPI app, 2 routers (facturas + emisor)
  config.py            Settings con prefijo FACT_
  database.py          async engine + sessionmaker
  models/              5 modelos: Emisor, Serie, Factura, FacturaLinea, RegistroVeriFactu
  routers/             emisor.py, facturas.py
  schemas/             emisor.py, factura.py (Pydantic v2)
  services/            factura_service, impuestos, numeracion, pdf, verifactu
migrations/
  versions/001_initial.py
tests/                 3 ficheros (SQLite in-memory)
```

## Stack

- Python 3.12 + FastAPI + SQLAlchemy async + asyncpg + Alembic
- ReportLab (PDF)
- Docker: postgres:16-alpine + app, puerto 8200:8000

## ALERTA DE SEGURIDAD

### python-jose debe reemplazarse
`requirements.txt` declara `python-jose[cryptography]>=3.3`. Esta librería está abandonada y tiene CVEs abiertos (CVE-2024-33664, CVE-2024-33663). Reemplazar por `PyJWT>=2.8`.

### X-Tenant-Id sin autenticación
Los routers leen `X-Tenant-Id` del header HTTP sin validar JWT. Cualquier cliente puede suplantar cualquier tenant. `FACT_JWT_PUBLIC_KEY` está en config pero no se usa en ningún router. Implementar middleware JWT que extraiga tenant_id del claim.

## Reglas

### R1 — Cadena VeriFactu inmutable
`verifactu.py` genera SHA-256 encadenado (`hash_anterior` → `hash_registro`). Una vez emitida, la factura no se modifica. `build_chained_record()` es la función crítica.

### R2 — Numeración con SELECT FOR UPDATE
`numeracion.py` usa SELECT FOR UPDATE sobre `SerieFacturacion.ultimo_numero`. No cambiar a optimistic locking — la numeración fiscal debe ser estrictamente secuencial sin huecos.

### R3 — Máquina de estados
`factura_service.py` define `_TRANSICIONES`: borrador→emitida, emitida→pagada, borrador→cancelada, emitida→cancelada. No añadir transiciones sin validar contra la normativa (RD 1007/2023).

### R4 — Sleep frágil en Docker
`docker-compose.yml` usa `sleep 2` antes de Alembic en vez de healthcheck en PG. Cambiar a `depends_on` con `condition: service_healthy`.

## Qué NO hacer

- No usar python-jose. Reemplazar por PyJWT.
- No aceptar tenant_id de headers sin JWT validado.
- No crear facturas con numeración fuera de secuencia.
- No modificar hashes VeriFactu de facturas emitidas.
- No hacer `alembic downgrade` en producción sin backup.
