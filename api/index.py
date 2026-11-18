from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI(redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # MUST be False for local files
    allow_methods=["*"],
    allow_headers=["*"],
)

UPSTREAM = "https://api.inferenceport.ai"

@app.get("/")
async def root():
    return {"status": "Proxy is running successfully!", "test_url": "/v1/models"}

@app.api_route("/v1/{path:path}", methods=["GET", "POST", "OPTIONS"])
async def proxy(path: str, request: Request):
    if request.method == "OPTIONS":
        return JSONResponse(content={}, status_code=200)

    url = f"{UPSTREAM}/v1/{path}"
    body = await request.body()
    
    headers = {
        k: v for k, v in request.headers.items() 
        if k.lower() not in ["host", "content-length", "connection"]
    }
    
    try:
        # 9 second timeout to prevent Vercel's 10s hard crash
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
