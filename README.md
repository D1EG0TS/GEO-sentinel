# GEO-sentinel

Microservicio de Geolocalización y Auditoría para Tecnología Electromecánica y Exproof.

Desarrollado por Diego Terrazas - Vive Codder

## Descripción

Sistema de captura invisible de IPs con geolocalización mediante IPinfo.io.

## Stack Tecnológico

- FastAPI (Python 3.10+)
- SQLite
- IPinfo.io API
- PM2 (gestión de procesos)

## Endpoints

- `GET /view-isologo` - Captura datos y redirige a imagen
- `GET /get-test-results` - Panel de auditoría
- `GET /health` - Health check
- `GET /t.png` - Píxel de rastreo

## Instalación

```bash
pip3 install -r requirements.txt
python3 init_db.py
pm2 start ecosystem.config.js
```

## Uso

Enviar enlace a tu jefe:
```
http://TU-VPS:8080/view-isologo
```

Revisar resultados:
```
http://TU-VPS:8080/get-test-results
```

## Licencia

Proyecto privado - Uso interno autorizado.
