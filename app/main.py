from fastapi import FastAPI

from app.routers import emisor, facturas

app = FastAPI(
    title="Tacholil Facturacion API",
    version="0.1.0",
    openapi_tags=[
        {"name": "facturas", "description": "CRUD facturas + emitir/pagar/anular/pdf"},
        {"name": "emisor", "description": "Datos fiscales del emisor"},
    ],
)

app.include_router(facturas.router)
app.include_router(emisor.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
