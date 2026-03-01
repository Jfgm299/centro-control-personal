from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from .core import engine, Base, settings
from app.core import auth
from app.core.module_loader import import_module

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)

# ── Cargar módulos dinámicamente ──────────────────────────────────────────────
loaded_modules = [('auth', auth)]
for module_name in settings.INSTALLED_MODULES:
    try:
        mod = import_module(module_name)
        loaded_modules.append((module_name, mod))
    except ImportError as e:
        print(f"❌ Error importando módulo '{module_name}': {e}")

all_tags = [tag for _, mod in loaded_modules if hasattr(mod, 'TAGS') for tag in mod.TAGS]
all_tag_groups = [mod.TAG_GROUP for _, mod in loaded_modules if hasattr(mod, 'TAG_GROUP')]

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Centro Control",
    description="Tu plataforma personal modular",
    docs_url="/docs",
    redoc_url=None,
    version="1.0.0",
    openapi_tags=all_tags,
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    schema = get_openapi(
        title=app.title, version=app.version,
        routes=app.routes, tags=app.openapi_tags,
    )
    schema["x-tagGroups"] = all_tag_groups
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Handlers y routers — completamente automáticos ───────────────────────────
for module_name, module in loaded_modules:
    # Registrar exception handlers si el módulo los exporta
    if hasattr(module, 'register_handlers'):
        module.register_handlers(app)

    if not hasattr(module, 'router'):
        print(f"⚠️  Módulo '{module_name}' no exporta 'router'")
        continue
    app.include_router(module.router, prefix=f'/api/{settings.API_VERSION}')
    print(f"✅ Módulo '{module_name}' cargado correctamente")

print(f"\n✅ {len(loaded_modules)} módulos cargados\n")

# ── Endpoints base ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "API working", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/v1/modules")
def get_modules():
    return {"modules": settings.INSTALLED_MODULES}

@app.get("/redoc", include_in_schema=False)
def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Centro Control — Docs",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
    )