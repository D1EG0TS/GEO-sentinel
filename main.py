#!/usr/bin/env python3
"""
================================================================================
SENTINEL-GEO v2.0
Microservicio de Geolocalización y Auditoría con GPS para Tecnología Electromecánica
================================================================================
Autor: Diego Terrazas - Vive Codder
Versión: 2.0.0
Fecha: Mayo 2026

Descripción:
Microservicio FastAPI para capturar y auditar accesos con geolocalización precisa.
Integración con IPinfo.io + Geolocalización GPS HTML5 para precisión de metros.

Características v2.0:
- Captura de IPs y metadatos
- Consulta en tiempo real con IPinfo.io
- Geolocalización GPS precisa (HTML5) - NUEVO
- Validación obligatoria de ubicación
- Interfaz profesional con diálogo de confirmación
- Panel de auditoría con datos GPS precisos
- Totalmente aislado del sistema principal

Stack: FastAPI + SQLite + IPinfo + Jinja2 + Uvicorn
================================================================================
"""

import os
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, Query, Form
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
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
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "sentinel_default_key")
DB_NAME = "sentinel.db"

# URL de la imagen corporativa de Exproof
IMAGE_URL = "https://exprooftecmx.tech/images/isologo_exproof.webp"

# Configurar templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

def render_template(template_name: str, **kwargs) -> str:
    """
    Renderiza un template HTML reemplazando variables
    """
    template_path = os.path.join(TEMPLATES_DIR, template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Reemplazar variables {{ variable }}
    for key, value in kwargs.items():
        html = html.replace(f"{{{{ {key} }}}}", str(value))
    
    return html

# Inicializar cliente IPinfo
ipinfo_handler = None
if IPINFO_TOKEN:
    try:
        ipinfo_handler = ipinfo.getHandler(IPINFO_TOKEN)
        print(f"✅ Cliente IPinfo inicializado correctamente")
    except Exception as e:
        print(f"⚠️  Error al inicializar IPinfo: {e}")
        ipinfo_handler = None
else:
    print(f"⚠️  No se encontró token de IPinfo. Funcionando en modo básico.")


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class GPSData(BaseModel):
    """
    Modelo para datos GPS del navegador
    """
    lat: float              # Latitud GPS
    lon: float              # Longitud GPS
    accuracy: float         # Precisión en metros
    ip: str                 # IP del cliente para asociar con registro


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_client_ip(request: Request) -> str:
    """
    Extrae la IP real del cliente, manejando proxies y cabeceras X-Forwarded-For
    """
    # Intentar obtener de X-Forwarded-For (para proxies/VPS)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # La primera IP es la del cliente original
        return forwarded_for.split(",")[0].strip()
    
    # Intentar X-Real-IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Fallback a la IP de conexión directa
    if request.client:
        return request.client.host
    
    return "unknown"


def detect_isp_type(org: str) -> str:
    """
    Detecta si el ISP es móvil o fijo basado en el nombre de la organización
    """
    if not org:
        return "unknown"
    
    org_lower = org.lower()
    
    # Palabras clave para redes móviles en México y LATAM
    mobile_keywords = [
        "telcel", "at&t", "movistar", "virgin", "freedom", "unefon",
        "weex", "flash mobile", "bait", "diri", "altan", "nokia solutions"
    ]
    
    # Palabras clave para redes fijas/empresariales
    fixed_keywords = [
        "totalplay", "telmex", "megacable", "axtel", "izzi", "infinitum",
        "bestel", "marcatel", "maxcom", "cablecom", "telecable"
    ]
    
    for keyword in mobile_keywords:
        if keyword in org_lower:
            return "mobile"
    
    for keyword in fixed_keywords:
        if keyword in org_lower:
            return "fixed"
    
    return "unknown"


def is_likely_vpn(org: str, hostname: str) -> bool:
    """
    Detecta si la conexión podría ser a través de VPN
    """
    if not org:
        return False
    
    vpn_keywords = [
        "vpn", "proxy", "tunnel", "nord", "expressvpn", "surfshark",
        "cyberghost", "private internet access", "proton", "hide.me"
    ]
    
    combined = f"{org} {hostname}".lower()
    
    for keyword in vpn_keywords:
        if keyword in combined:
            return True
    
    return False


def format_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Extrae información legible del User-Agent
    """
    if not user_agent:
        return {"device": "unknown", "browser": "unknown", "os": "unknown"}
    
    ua_lower = user_agent.lower()
    
    # Detectar dispositivo
    if "mobile" in ua_lower:
        device = "Mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device = "Tablet"
    else:
        device = "Desktop"
    
    # Detectar navegador
    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "Chrome"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "edg" in ua_lower:
        browser = "Edge"
    else:
        browser = "Other"
    
    # Detectar SO
    if "windows" in ua_lower:
        os_name = "Windows"
    elif "mac" in ua_lower or "darwin" in ua_lower:
        os_name = "macOS"
    elif "linux" in ua_lower:
        os_name = "Linux"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "ios" in ua_lower or "iphone" in ua_lower:
        os_name = "iOS"
    else:
        os_name = "Unknown"
    
    return {
        "device": device,
        "browser": browser,
        "os": os_name,
        "full": user_agent[:200]  # Truncado para BD
    }


async def get_ipinfo_data(ip_address: str) -> Dict[str, Any]:
    """
    Consulta IPinfo.io para obtener datos de geolocalización
    Con manejo de errores y fallback a modo básico
    """
    if not IPINFO_TOKEN or not ipinfo_handler:
        return {
            "city": "unknown",
            "region": "unknown", 
            "country": "unknown",
            "org": "unknown",
            "loc": "unknown",
            "timezone": "unknown",
            "postal": "unknown",
            "hostname": "unknown"
        }
    
    try:
        # Intentar con la librería ipinfo oficial
        details = ipinfo_handler.getDetails(ip_address)
        
        return {
            "city": getattr(details, "city", "unknown"),
            "region": getattr(details, "region", "unknown"),
            "country": getattr(details, "country_name", getattr(details, "country", "unknown")),
            "org": getattr(details, "org", "unknown"),
            "loc": getattr(details, "loc", "unknown"),
            "timezone": getattr(details, "timezone", "unknown"),
            "postal": getattr(details, "postal", "unknown"),
            "hostname": getattr(details, "hostname", "unknown")
        }
    except Exception as e:
        print(f"⚠️  Error consultando IPinfo (librería): {e}")
        
        # Fallback: Intentar con HTTP directo
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                url = f"https://ipinfo.io/{ip_address}/json?token={IPINFO_TOKEN}"
                response = await client.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "city": data.get("city", "unknown"),
                        "region": data.get("region", "unknown"),
                        "country": data.get("country", "unknown"),
                        "org": data.get("org", "unknown"),
                        "loc": data.get("loc", "unknown"),
                        "timezone": data.get("timezone", "unknown"),
                        "postal": data.get("postal", "unknown"),
                        "hostname": data.get("hostname", "unknown")
                    }
        except Exception as e2:
            print(f"⚠️  Error en fallback HTTP: {e2}")
        
        # Si todo falla, retornar datos básicos
        return {
            "city": "unknown",
            "region": "unknown",
            "country": "unknown", 
            "org": "unknown",
            "loc": "unknown",
            "timezone": "unknown",
            "postal": "unknown",
            "hostname": "unknown"
        }


def save_access_log(data: Dict[str, Any]) -> int:
    """
    Guarda el registro de acceso en SQLite
    Retorna el ID del registro creado
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
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
            data.get("isp_type"),
            data.get("coordinates"),
            data.get("timezone"),
            data.get("postal_code"),
            data.get("is_vpn", False),
            data.get("is_mobile", False),
            data.get("status", "pending_gps"),
            data.get("location_method", "ip"),
            data.get("permission_granted", False),
            json.dumps(data.get("raw_data", {})),
            data.get("timestamp")
        ))
        
        last_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return last_id
    except Exception as e:
        print(f"❌ Error guardando en BD: {e}")
        return -1


def update_gps_data(ip_address: str, gps_data: GPSData) -> bool:
    """
    Actualiza el registro existente con datos GPS precisos
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Buscar el último registro de esa IP con status 'pending_gps'
        cursor.execute('''
            SELECT id FROM access_logs 
            WHERE ip_address = ? AND status = 'pending_gps'
            ORDER BY id DESC LIMIT 1
        ''', (ip_address,))
        
        row = cursor.fetchone()
        
        if not row:
            # Si no hay registro pending, buscar cualquiera de esa IP
            cursor.execute('''
                SELECT id FROM access_logs 
                WHERE ip_address = ?
                ORDER BY id DESC LIMIT 1
            ''', (ip_address,))
            row = cursor.fetchone()
        
        if row:
            record_id = row[0]
            
            # Actualizar con datos GPS
            cursor.execute('''
                UPDATE access_logs 
                SET gps_lat = ?,
                    gps_lon = ?,
                    gps_accuracy = ?,
                    coordinates = ?,
                    location_method = 'gps',
                    status = 'gps_verified',
                    permission_granted = 1,
                    gps_timestamp = ?
                WHERE id = ?
            ''', (
                gps_data.lat,
                gps_data.lon,
                gps_data.accuracy,
                f"{gps_data.lat},{gps_data.lon}",
                datetime.now().isoformat(),
                record_id
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ GPS actualizado para registro {record_id}: {gps_data.lat}, {gps_data.lon} (±{gps_data.accuracy}m)")
            return True
        else:
            conn.close()
            print(f"⚠️  No se encontró registro para IP {ip_address}")
            return False
            
    except Exception as e:
        print(f"❌ Error actualizando GPS: {e}")
        return False


# ============================================================================
# INICIALIZACIÓN DE FASTAPI
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación
    """
    # Startup
    print("🚀 Iniciando Sentinel-Geo v2.0...")
    print(f"📍 Base de datos: {DB_NAME}")
    print(f"🔌 Puerto: {PORT}")
    print(f"🌐 CORS: {CORS_ORIGINS}")
    print(f"🔑 IPinfo: {'Configurado' if IPINFO_TOKEN else 'No configurado'}")
    print(f"📁 Templates: {TEMPLATES_DIR}")
    yield
    # Shutdown
    print("👋 Sentinel-Geo detenido")


app = FastAPI(
    title="Sentinel-Geo v2.0",
    description="Microservicio de Geolocalización y Auditoría con GPS - Tecnología Electromecánica",
    version="2.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Endpoint raíz - Información del servicio
    """
    return {
        "service": "Sentinel-Geo",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Geolocalización por IP (IPinfo)",
            "Geolocalización GPS precisa (HTML5)",
            "Validación obligatoria de ubicación"
        ],
        "endpoints": {
            "view_isologo": "/view-isologo - Validación GPS + redirección",
            "update_precise_location": "POST /update-precise-location - Actualizar GPS",
            "test_results": "/get-test-results - Panel de auditoría",
            "health": "/health - Estado del servicio"
        }
    }


@app.get("/health")
async def health_check():
    """
    Verificación de salud del servicio
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": os.path.exists(DB_NAME),
        "ipinfo_configured": bool(IPINFO_TOKEN),
        "version": "2.0.0"
    }


@app.get("/view-isologo")
async def view_isologo(request: Request):
    """
    ENDPOINT PRINCIPAL CON VALIDACIÓN GPS
    
    Muestra interfaz HTML que solicita validación GPS antes de redirigir
    a la imagen corporativa. Captura datos IP primero, luego espera GPS preciso.
    """
    # 1. Capturar IP real del cliente
    client_ip = get_client_ip(request)
    
    # 2. Capturar User-Agent
    user_agent = request.headers.get("user-agent", "")
    ua_info = format_user_agent(user_agent)
    
    print(f"🔍 Acceso detectado desde IP: {client_ip}")
    
    # 3. Consultar IPinfo.io para geolocalización inicial
    geo_data = await get_ipinfo_data(client_ip)
    
    # 4. Detectar tipo de red (móvil/fija)
    isp_type = detect_isp_type(geo_data.get("org", ""))
    
    # 5. Detectar posible VPN
    is_vpn = is_likely_vpn(
        geo_data.get("org", ""),
        geo_data.get("hostname", "")
    )
    
    # 6. Preparar datos para guardar (estado: esperando GPS)
    log_data = {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "city": geo_data.get("city"),
        "region": geo_data.get("region"),
        "country": geo_data.get("country"),
        "org": geo_data.get("org"),
        "isp_type": isp_type,
        "coordinates": geo_data.get("loc"),  # Coordenadas aproximadas por IP
        "timezone": geo_data.get("timezone"),
        "postal_code": geo_data.get("postal"),
        "is_vpn": is_vpn,
        "is_mobile": isp_type == "mobile",
        "status": "pending_gps",
        "location_method": "ip",
        "permission_granted": False,
        "raw_data": {
            "ua_info": ua_info,
            "ipinfo_response": geo_data,
            "headers": dict(request.headers)
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # 7. Guardar en base de datos
    record_id = save_access_log(log_data)
    
    if record_id > 0:
        print(f"✅ Registro creado #{record_id}: {client_ip} ({geo_data.get('city')}, {geo_data.get('region')}) - Esperando GPS...")
    else:
        print(f"⚠️  No se pudo guardar el registro para {client_ip}")
    
    # 8. Retornar interfaz HTML para validación GPS
    html_content = render_template("validador.html", 
                                   client_ip=client_ip,
                                   image_url=IMAGE_URL)
    return HTMLResponse(content=html_content)


@app.post("/update-precise-location")
async def update_precise_location(data: GPSData):
    """
    ENDPOINT POST: Actualizar ubicación precisa con GPS
    
    Recibe coordenadas GPS del navegador y actualiza el registro existente.
    """
    print(f"📍 Recibiendo datos GPS de {data.ip}: {data.lat}, {data.lon} (±{data.accuracy}m)")
    
    # Actualizar el registro existente
    success = update_gps_data(data.ip, data)
    
    if success:
        return {
            "success": True,
            "message": "Ubicación actualizada exitosamente",
            "redirect_url": IMAGE_URL,
            "data": {
                "lat": data.lat,
                "lon": data.lon,
                "accuracy": data.accuracy,
                "ip": data.ip
            }
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="No se encontró registro para actualizar"
        )


@app.get("/get-test-results")
async def get_test_results(limit: int = Query(50, ge=1, le=100)):
    """
    Endpoint para ver los resultados con datos GPS precisos
    
    Devuelve los últimos N accesos registrados con información completa
    de geolocalización (IP + GPS).
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM access_logs 
            ORDER BY id DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convertir a lista de diccionarios
        results = []
        for row in rows:
            row_dict = dict(row)
            # Parsear raw_data si existe
            if row_dict.get("raw_data"):
                try:
                    row_dict["raw_data"] = json.loads(row_dict["raw_data"])
                except:
                    pass
            results.append(row_dict)
        
        # Estadísticas adicionales
        stats = {
            "total_registros": len(results),
            "con_gps_preciso": sum(1 for r in results if r.get("location_method") == "gps"),
            "pendientes_gps": sum(1 for r in results if r.get("status") == "pending_gps"),
            "dispositivos_moviles": sum(1 for r in results if r.get("is_mobile")),
            "posibles_vpn": sum(1 for r in results if r.get("is_vpn")),
            "timestamp_consulta": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "stats": stats,
            "registros": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error consultando base de datos: {str(e)}"
        )


@app.get("/t.png")
async def tracking_pixel(request: Request):
    """
    Endpoint de píxel de rastreo transparente (1x1)
    """
    # Capturar datos (misma lógica que view-isologo pero sin esperar GPS)
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    geo_data = await get_ipinfo_data(client_ip)
    isp_type = detect_isp_type(geo_data.get("org", ""))
    
    log_data = {
        "ip_address": client_ip,
        "user_agent": user_agent,
        "city": geo_data.get("city"),
        "region": geo_data.get("region"),
        "country": geo_data.get("country"),
        "org": geo_data.get("org"),
        "isp_type": isp_type,
        "coordinates": geo_data.get("loc"),
        "timezone": geo_data.get("timezone"),
        "postal_code": geo_data.get("postal"),
        "is_vpn": False,
        "is_mobile": isp_type == "mobile",
        "status": "pixel_captured",
        "location_method": "ip",
        "permission_granted": False,
        "raw_data": {"source": "tracking_pixel"},
        "timestamp": datetime.now().isoformat()
    }
    
    save_access_log(log_data)
    
    # Devolver píxel transparente PNG de 1x1
    pixel_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,
        0x89, 0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0x60, 0x60, 0x60, 0x60,
        0x00, 0x00, 0x00, 0x05, 0x00, 0x01, 0x0D, 0x0A,
        0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
    ])
    
    return JSONResponse(
        content=pixel_data,
        media_type="image/png",
        headers={"Content-Length": str(len(pixel_data))}
    )


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🛡️  SENTINEL-GEO v2.0")
    print("   Geolocalización Precisa con GPS")
    print("   Tecnología Electromecánica y Exproof")
    print("=" * 70)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True,
        log_level="info"
    )
