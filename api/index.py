from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPSTREAM = "https://api.wavespeed.ai/api/v3"
API_KEY = "wsk_live_wCnpzF9ESYtLd2aTOPRpeIXyfCGZ0PLvWIpBOm4OuZ8"

@app.api_route("/{path:path}", methods=["GET", "POST", "OPTIONS"])
async def proxy(path: str, request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(content={}, status_code=200)

    url = f"{UPSTREAM}/{path}"
    body = await request.body()
    
    headers = {
        k: v for k, v in request.headers.items() 
        if k.lower() not in ["host", "content-length", "connection"]
    }
    
    headers["Authorization"] = f"Bearer {API_KEY}"
    
    try:
        async with httpx.AsyncClient(timeout=9.0) as client:
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
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"error": "Upstream AI is taking too long."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
