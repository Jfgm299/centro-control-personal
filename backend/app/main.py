from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import expenses_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Centro Control",
    description= 'prueba',
    version='1.0.0'
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"]
)

app.include_router(expenses_router, prefix='/api')

@app.get("/")
def root():
    return {"message": "API working", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

