from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import socket
import asyncio

app = FastAPI()

# Função para resolver DNS de forma assíncrona
async def async_gethostbyname(domain: str) -> str:
    loop = asyncio.get_event_loop()
    try:
        ip = await loop.run_in_executor(None, socket.gethostbyname, domain)
        return ip
    except socket.gaierror:
        raise

@app.get("/resolve")
async def resolve(domain: str = Query(..., description="Domínio para resolver")):
    try:
        ip = await async_gethostbyname(domain)
        return {"domain": domain, "ip": ip}
    except socket.gaierror:
        return JSONResponse(
            status_code=500,
            content={"error": f"Não foi possível resolver '{domain}'"}
        )

# Para rodar com uvicorn:
# uvicorn nome_do_arquivo:app --host 0.0.0.0 --port 8000 --reload
