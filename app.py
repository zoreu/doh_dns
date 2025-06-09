from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
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

@app.post("/dns-query")
async def dns_query(request: Request):
    if request.headers.get("content-type") != "application/dns-message":
        return Response(status_code=415, content="Unsupported Media Type")

    dns_query = await request.body()

    try:
        query = DNSRecord.parse(dns_query)
        qname = str(query.q.qname)
        qtype = QTYPE[query.q.qtype]

        ip = socket.gethostbyname(qname)

        reply = query.reply()
        reply.add_answer(*DNSRecord.question(qname).add_answer_a(ip))

        return Response(content=reply.pack(), media_type="application/dns-message")
    except Exception as e:
        return Response(status_code=500, content=f"DNS resolution failed: {str(e)}")

@app.get("/")
async def root():
    return {"status": "DNS over HTTPS server is running"}

# Para rodar com uvicorn:
# uvicorn nome_do_arquivo:app --host 0.0.0.0 --port 8000 --reload
