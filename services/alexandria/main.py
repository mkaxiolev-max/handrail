from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.sources import router as sources_router
from routes.atoms import router as atoms_router
from routes.graph import router as graph_router
from routes.ingest import router as ingest_router
from routes.documents import router as documents_router

app = FastAPI(title="Alexandria", version="1.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources_router)
app.include_router(atoms_router)
app.include_router(graph_router)
app.include_router(ingest_router)
app.include_router(documents_router)

@app.get("/healthz")
async def health():
    return {"status": "ok", "service": "alexandria"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
