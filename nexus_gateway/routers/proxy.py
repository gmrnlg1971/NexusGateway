from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
import httpx
from pydantic import BaseModel
from typing import List, Optional, Any, AsyncGenerator

from nexus_gateway.core.balancer import balancer
from nexus_gateway.core.rate_limit import limiter
from nexus_gateway.core.config import settings

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7

async def verify_rate_limit(request: Request) -> str:
    """
    Dependency function to verify if the incoming request exceeds the rate limit.
    """
    # In a real app, extract user_id from auth token. Here we use IP for demo.
    client_host = request.client.host if request.client else "unknown"
    user_id = str(client_host)
    if await limiter.is_rate_limited(user_id, limit=settings.rate_limit_rpm):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return user_id

@router.post("/v1/chat/completions")
async def chat_completions(
    request: Request, 
    user_id: str = Depends(verify_rate_limit)
) -> Any:
    """
    Proxies request to the optimal vLLM node based on semantic KV cache routing.
    
    Args:
        request: The FastAPI incoming request.
        user_id: Validated user identifier from rate limiting.
        
    Returns:
        JSON response or StreamingResponse.
    """
    payload = await request.json()
    chat_req = ChatCompletionRequest(**payload)

    # 1. Extract context for routing (isolate system prompt)
    system_messages = [m.content for m in chat_req.messages if m.role == "system"]
    if system_messages:
        full_prompt = "\n".join(system_messages)
    else:
        full_prompt = "\n".join([m.content for m in chat_req.messages])
    
    # 2. Get optimal KV-cache aware node
    target_node = balancer.get_node(full_prompt)
    url = f"{target_node}/v1/chat/completions"

    # 3. Proxy request asynchronously using global client
    client = request.app.state.http_client
    
    if chat_req.stream:
        async def stream_generator() -> AsyncGenerator[str, None]:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    yield f"data: {{\"error\": \"Upstream error {response.status_code}\"}}\n\n"
                    return
                async for chunk in response.aiter_text():
                    yield chunk
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    else:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Upstream vLLM error")
        return response.json()
