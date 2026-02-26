from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .modules.expenses_tracker.expenses_router import router as expenses_router
from .modules.gym_tracker.routers import workouts_router, exercises_router, sets_router, body_measurements_router
from .modules.gym_tracker.handlers import register_exception_handlers

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


app.include_router(expenses_router, prefix='/api')
app.include_router(workouts_router, prefix="/api")
app.include_router(exercises_router, prefix='/api')
app.include_router(sets_router,prefix='/api')
app.include_router(body_measurements_router, prefix='/api')

@app.get("/")
def root():
    return {"message": "API working", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

