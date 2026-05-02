# GEO-sentinel

Microservicio de Geolocalización y Auditoría con GPS Preciso para Tecnología Electromecánica y Exproof.

**Versión 2.0** - Ahora con geolocalización GPS de alta precisión (HTML5)

---

## 🚀 Características

- ✅ **Geolocalización por IP** (IPinfo.io)
- ✅ **Geolocalización GPS Precisa** (HTML5 Geolocation API)
- ✅ **Validación Obligatoria** de ubicación antes de acceder
- ✅ **Interfaz Profesional** con diálogo de confirmación
- ✅ **Precisión de metros** en coordenadas GPS
- ✅ **Panel de Auditoría** completo

---

## 📋 Stack Tecnológico

- FastAPI (Python 3.10+)
- SQLite
- IPinfo.io API
- Jinja2 Templates
- HTML5 Geolocation API
- PM2 (gestión de procesos)

---

## 🔗 Endpoints

### Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/view-isologo` | GET | Interfaz de validación GPS + redirección |
| `/update-precise-location` | POST | Recibe datos GPS del navegador |
| `/get-test-results` | GET | Panel de auditoría con datos GPS |
| `/health` | GET | Health check del servicio |
| `/t.png` | GET | Píxel de rastreo transparente |

---

## 📦 Instalación

### Requisitos

- Python 3.10+
- pip3
- PM2 (para producción)

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/D1EG0TS/GEO-sentinel.git
cd GEO-sentinel

# 2. Instalar dependencias
pip3 install --break-system-packages -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu token de IPinfo

# 4. Inicializar base de datos
python3 init_db.py
# Responder 's' para crear nueva BD

# 5. Iniciar con PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### Despliegue Automatizado

```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 🎯 Uso

### Para tu Jefe (Demo):

Envía este enlace:
```
http://TU-VPS:8080/view-isologo
```

**Flujo:**
1. Verá interfaz profesional de Exproof
2. Presiona "Validar Mi Ubicación"
3. Diálogo: "¿Continuar al sitio?" → **Confirmar**
4. Navegador pide permiso GPS → **Permitir**
5. Sistema captura coordenadas precisas (±5 metros)
6. Redirige a imagen real

### Para ti (Panel de Auditoría):

```
http://TU-VPS:8080/get-test-results
```

**Datos capturados:**
- IP del cliente
- Ciudad/Estado/ País (IPinfo)
- **Coordenadas GPS precisas** (lat, lon)
- **Precisión en metros**
- ISP/Organización
- Tipo de red (móvil/fija)
- Dispositivo y navegador
- Timestamp

---

## 🎨 Flujo de Validación

```
Usuario → /view-isologo
    ↓
Página HTML (interfaz Exproof)
    ↓
"Validar Mi Ubicación" (botón)
    ↓
Modal: "¿Continuar al sitio?"
    ↓
[Confirmar] o [Cancelar]
    ↓
GPS nativo: "¿Permitir acceso a ubicación?"
    ↓
Captura coordenadas precisas
    ↓
POST a /update-precise-location
    ↓
BD actualizada (status: gps_verified)
    ↓
Redirección a imagen real
```

---

## 🛠️ Comandos PM2

```bash
# Ver estado
pm2 status

# Ver logs en tiempo real
pm2 logs sentinel-geo

# Reiniciar servicio
pm2 restart sentinel-geo

# Detener servicio
pm2 stop sentinel-geo
```

---

## 🔐 Configuración

### Variables de Entorno (.env)

```bash
# Token de IPinfo.io (obtén gratis en https://ipinfo.io/signup)
IPINFO_TOKEN=tu_token_aqui

# Puerto del servicio
PORT=8080

# CORS ("*" para cualquier origen)
CORS_ORIGINS=*

# Clave API para futuras protecciones
API_KEY_SECRET=tu_clave_secreta
```

---

## 📝 Estructura de Datos

### Registro de Acceso (access_logs)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER | ID único |
| `ip_address` | TEXT | IP del cliente |
| `gps_lat` | REAL | Latitud GPS |
| `gps_lon` | REAL | Longitud GPS |
| `gps_accuracy` | REAL | Precisión en metros |
| `location_method` | TEXT | 'ip' o 'gps' |
| `status` | TEXT | 'pending_gps' o 'gps_verified' |
| `timestamp` | TEXT | Fecha y hora |

---

## 💬 Mensaje para Demo

> *"Ingeniero, le comparto el enlace al isologo actualizado. 
> Por nuevas políticas de seguridad, necesitará validar su ubicación 
> para acceder: http://TU-VPS:8080/view-isologo"*

### Presentación de Impacto:

Después de que acceda:

> *"Como puede ver, el sistema capturó su ubicación con precisión de **X metros** 
> usando GPS satelital. Esta es la base de nuestro nuevo sistema de seguridad 
> perimetral para validar que el personal operativo accede desde ubicaciones 
> autorizadas."*

---

## 👨‍💻 Autor

**Diego Terrazas** - *Vive Codder*

Desarrollado para **Tecnología Electromecánica y Exproof**

---

## 📄 Licencia

Proyecto privado - Uso interno autorizado.

---

<div align="center">

**🛡️ Sentinel-Geo v2.0 - Geolocalización Precisa**

*Seguridad perimetral inteligente con GPS*

</div>
