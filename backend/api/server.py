from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
app = FastAPI(
    title="Helios Recruiter Intelligence",
    description="AI-powered candidate ranking engine",
    version="1.0.0",
)

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {
        "message": "Helios Recruiter Intelligence API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}