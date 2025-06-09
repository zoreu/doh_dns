from fastapi import FastAPI, Query, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
import socket
import asyncio
from dnslib import DNSRecord, QTYPE
import dns.resolver

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

@app.get("/dns-query")
async def dns_query_json(
    name: str = Query(...),
    type: str = Query("A"),
    request: Request = None
):
    # Verifica se o header Accept é DNS JSON (usado por curl/firefox/chrome)
    if "application/dns-json" not in request.headers.get("accept", ""):
        return Response(status_code=406, content="Not Acceptable")

    try:
        # Faz a resolução usando dnspython
        resolver = dns.resolver.Resolver()
        qtype = type.upper()
        answer = resolver.resolve(name, qtype)

        # Constrói a resposta no formato RFC 8484
        result = {
            "Status": 0,
            "TC": False,
            "RD": True,
            "RA": True,
            "AD": False,
            "CD": False,
            "Question": [{"name": name, "type": dns.rdatatype.from_text(qtype)}],
            "Answer": [
                {
                    "name": name,
                    "type": dns.rdatatype.from_text(qtype),
                    "TTL": r.ttl,
                    "data": r.to_text()
                } for r in answer
            ]
        }
        return JSONResponse(content=result)
    except dns.resolver.NoAnswer:
        return JSONResponse(content={"Status": 3, "Question": [{"name": name, "type": dns.rdatatype.from_text(type)}]})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/")
async def root():
    return {"status": "DNS over HTTPS server is running"}

# Para rodar com uvicorn:
# uvicorn nome_do_arquivo:app --host 0.0.0.0 --port 8000 --reload
