from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()
UPSTREAM = "https://api.inferenceport.ai"

@app.api_route("/v1/{path:path}", methods=["GET", "POST"])
async def proxy(path: str, request: Request):
    url = f"{UPSTREAM}/v1/{path}"
    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items() 
        if k.lower() not in ["host", "content-length", "connection"]
    }
    async with httpx.AsyncClient(timeout=55.0) as client:
        req = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
        resp = await client.send(req, stream=True)
        return StreamingResponse(
            resp.aiter_raw(),
            status_code=resp.status_code,
            headers=dict(resp.headers)
        )
