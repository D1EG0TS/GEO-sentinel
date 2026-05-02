#!/usr/bin/env python3
"""
================================================================================
SENTINEL-GEO v2.0 - SIMPLIFICADO
Microservicio de Geolocalización con GPS para Tecnología Electromecánica
================================================================================
Autor: Diego Terrazas - Vive Codder
Versión: 2.0.1 (Simplificado)
Fecha: Mayo 2026
================================================================================
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import httpx
import ipinfo

# Cargar variables de entorno
load_dotenv()

# Configuración
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")
PORT = int(os.getenv("PORT", 8080))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
DB_NAME = "sentinel.db"

# URL de la imagen corporativa de Exproof
IMAGE_URL = "https://exprooftecmx.tech/images/isologo_exproof.webp"

# Configurar templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Inicializar cliente IPinfo
ipinfo_handler = None
if IPINFO_TOKEN:
    try:
        ipinfo_handler = ipinfo.getHandler(IPINFO_TOKEN)
        print("✅ Cliente IPinfo inicializado correctamente")
    except Exception as e:
        print(f"⚠️  Error al inicializar IPinfo: {e}")
        ipinfo_handler = None

# ============================================================================
# MODELOS
# ============================================================================

class GPSData(BaseModel):
    lat: float
    lon: float
    accuracy: float
    ip: str

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_client_ip(request: Request) -> str:
    """Extrae la IP real del cliente"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"

def render_template(template_name: str, **kwargs) -> str:
    """Renderiza template reemplazando {{ variable }}"""
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    for key, value in kwargs.items():
        html = html.replace("{{ " + key + " }}", str(value))
    
    return html

async def get_ipinfo(ip: str) -> Dict[str, Any]:
    """Consulta IPinfo.io"""
    if not IPINFO_TOKEN or not ipinfo_handler:
        return {"city": "unknown", "region": "unknown", "country": "unknown", 
                "org": "unknown", "loc": "unknown"}
    
    try:
        details = ipinfo_handler.getDetails(ip)
        return {
            "city": getattr(details, "city", "unknown"),
            "region": getattr(details, "region", "unknown"),
            "country": getattr(details, "country", "unknown"),
            "org": getattr(details, "org", "unknown"),
            "loc": getattr(details, "loc", "unknown")
        }
    except:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}")
                if r.status_code == 200:
                    d = r.json()
                    return {"city": d.get("city", "unknown"), "region": d.get("region", "unknown"),
                            "country": d.get("country", "unknown"), "org": d.get("org", "unknown"),
                            "loc": d.get("loc", "unknown")}
        except:
            pass
    return {"city": "unknown", "region": "unknown", "country": "unknown", 
            "org": "unknown", "loc": "unknown"}

def save_log(data: Dict[str, Any]) -> int:
    """Guarda en BD, retorna ID"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute('''
            INSERT INTO access_logs 
            (ip_address, user_agent, city, region, country, org, isp_type, 
             coordinates, timezone, postal_code, is_vpn, is_mobile, status, 
             location_method, permission_granted, raw_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get("ip_address"),
            data.get("user_agent"),
            data.get("city"),
            data.get("region"),
            data.get("country"),
            data.get("org"),
            data.get("isp_type", "unknown"),
            data.get("coordinates"),
            data.get("timezone", "unknown"),
            data.get("postal_code", "unknown"),
            data.get("is_vpn", False),
            data.get("is_mobile", False),
            data.get("status", "pending_gps"),
            data.get("location_method", "ip"),
            data.get("permission_granted", False),
            json.dumps(data.get("raw_data", {})),
            data.get("timestamp")
        ))
        lid = c.lastrowid
        conn.commit()
        conn.close()
        return lid
    except Exception as e:
        print(f"❌ Error BD: {e}")
        return -1

def update_gps(ip: str, gps: GPSData) -> bool:
    """Actualiza registro con datos GPS"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Buscar último registro de esa IP
        c.execute('SELECT id FROM access_logs WHERE ip_address = ? ORDER BY id DESC LIMIT 1', (ip,))
        row = c.fetchone()
        
        if row:
            rid = row[0]
            c.execute('''
                UPDATE access_logs 
                SET gps_lat = ?, gps_lon = ?, gps_accuracy = ?, 
                    coordinates = ?, location_method = 'gps', 
                    status = 'gps_verified', permission_granted = 1, gps_timestamp = ?
                WHERE id = ?
            ''', (gps.lat, gps.lon, gps.accuracy, f"{gps.lat},{gps.lon}", 
                 datetime.now().isoformat(), rid))
            conn.commit()
            conn.close()
            print(f"✅ GPS actualizado: {gps.lat}, {gps.lon} (±{gps.accuracy}m)")
            return True
        conn.close()
        return False
    except Exception as e:
        print(f"❌ Error actualizando GPS: {e}")
        return False

# ============================================================================
# FASTAPI
# ============================================================================

app = FastAPI(title="Sentinel-Geo v2.0", version="2.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"service": "Sentinel-Geo", "version": "2.0.1", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.1", "db": os.path.exists(DB_NAME)}

@app.get("/view-isologo")
async def view_isologo(request: Request):
    """Muestra modal de confirmación, luego redirige a imagen"""
    client_ip = get_client_ip(request)
    print(f"🔍 Acceso desde: {client_ip}")
    
    # Capturar datos IP
    ua = request.headers.get("user-agent", "")
    geo = await get_ipinfo(client_ip)
    
    # Guardar en BD
    data = {
        "ip_address": client_ip,
        "user_agent": ua,
        "city": geo.get("city"),
        "region": geo.get("region"),
        "country": geo.get("country"),
        "org": geo.get("org"),
        "coordinates": geo.get("loc"),
        "timestamp": datetime.now().isoformat(),
        "status": "pending_gps",
        "location_method": "ip",
        "raw_data": {"ua": ua, "geo": geo}
    }
    save_log(data)
    
    # Renderizar HTML (solo modal)
    html = render_template("validador.html", 
                          client_ip=client_ip,
                          image_url=IMAGE_URL)
    return HTMLResponse(content=html)

@app.post("/update-precise-location")
async def update_gps_endpoint(data: GPSData):
    """Recibe GPS del navegador y actualiza BD"""
    print(f"📍 GPS recibido de {data.ip}: {data.lat}, {data.lon} (±{data.accuracy}m)")
    success = update_gps(data.ip, data)
    
    if success:
        return {"success": True, "redirect_url": IMAGE_URL,
                "data": {"lat": data.lat, "lon": data.lon, "accuracy": data.accuracy}}
    else:
        raise HTTPException(status_code=404, detail="No se encontró registro")

@app.get("/get-test-results")
async def get_results():
    """Panel de auditoría"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM access_logs ORDER BY id DESC LIMIT 50')
        rows = c.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            d = dict(row)
            if d.get("raw_data"):
                try:
                    d["raw_data"] = json.loads(d["raw_data"])
                except:
                    pass
            results.append(d)
        
        return {"status": "success", "total": len(results), "registros": results}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🛡️  SENTINEL-GEO v2.0.1")
    print("=" * 60)
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
