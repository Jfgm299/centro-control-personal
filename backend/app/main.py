from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import expenses_router, workouts_router, exercises_router, sets_router, body_measurements_router
from .handlers import register_exception_handlers

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Centro Control",
    description= 'prueba',
    version='2.0.0'
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

