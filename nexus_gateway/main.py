from fastapi import FastAPI
from nexus_gateway.routers import proxy
from nexus_gateway.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="High-performance semantic load balancer and proxy for vLLM",
    version="1.0.0"
)

app.include_router(proxy.router, tags=["OpenAI Proxy"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nexus_gateway.main:app", host="0.0.0.0", port=8080, workers=4)
