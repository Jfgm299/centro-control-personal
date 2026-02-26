from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core import engine, Base
from .core import settings
#from .modules.expenses_tracker.expenses_router import router as expenses_router
#from .modules.gym_tracker.routers import workouts_router, exercises_router, sets_router, body_measurements_router
from .modules.gym_tracker.handlers import register_exception_handlers
from importlib import import_module

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Centro Control",
    description= 'prueba',
    version='2.0.1'
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)

register_exception_handlers(app)

for module_name in settings.INSTALLED_MODULES:
    try:
        module = import_module(f'app.modules.{module_name}')

        if not hasattr(module, 'router'):
            print(f"⚠️  Módulo '{module_name}' no exporta 'router'")
            continue
        
        app.include_router(
            module.router,
            prefix=f'/api/{settings.API_VERSION}'
        )
        print(f"✅ Módulo '{module_name}' cargado correctamente")
    
    except ImportError as e:
        print(f"❌ Error importando módulo '{module_name}': {e}")
    except Exception as e:
        print(f"❌ Error inesperado cargando '{module_name}': {e}")

print(f"\n✅ {len(settings.INSTALLED_MODULES)} módulos cargados\n")


# app.include_router(expenses_router, prefix='/api')
# app.include_router(workouts_router, prefix="/api")
# app.include_router(exercises_router, prefix='/api')
# app.include_router(sets_router,prefix='/api')
# app.include_router(body_measurements_router, prefix='/api')

@app.get("/")
def root():
    return {"message": "API working", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

