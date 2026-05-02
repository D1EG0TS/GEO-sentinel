#!/bin/bash
# =============================================================================
# SENTINEL-GEO - Script de Despliegue
# =============================================================================
# Autor: Diego Terrazas - Vive Codder
# Descripción: Script automatizado para desplegar el microservicio Sentinel-Geo
# =============================================================================

set -e  # Detener en caso de error

echo "🚀 =========================================================="
echo "🚀  SENTINEL-GEO - Script de Despliegue"
echo "🚀 =========================================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directorio del proyecto
PROJECT_DIR="/home/diego-terrazas/sentinel-geo"
cd "$PROJECT_DIR"

echo -e "${YELLOW}📁 Directorio de trabajo: $PROJECT_DIR${NC}"
echo ""

# =============================================================================
# PASO 1: Verificar dependencias
# =============================================================================
echo -e "${YELLOW}🔍 Paso 1: Verificando dependencias...${NC}"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no está instalado${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 no está instalado${NC}"
    exit 1
fi
echo -e "${GREEN}✅ pip3 disponible${NC}"

# Verificar PM2
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}⚠️  PM2 no está instalado. Instalando...${NC}"
    npm install -g pm2
fi
echo -e "${GREEN}✅ PM2 disponible${NC}"

echo ""

# =============================================================================
# PASO 2: Instalar dependencias Python
# =============================================================================
echo -e "${YELLOW}📦 Paso 2: Instalando dependencias Python...${NC}"

pip3 install -q -r requirements.txt

echo -e "${GREEN}✅ Dependencias instaladas${NC}"
echo ""

# =============================================================================
# PASO 3: Inicializar base de datos
# =============================================================================
echo -e "${YELLOW}🗄️  Paso 3: Inicializando base de datos...${NC}"

if [ -f "sentinel.db" ]; then
    echo -e "${YELLOW}⚠️  Base de datos existente encontrada${NC}"
    read -p "¿Deseas recrearla? (s/N): " response
    if [[ "$response" =~ ^[Ss]$ ]]; then
        rm -f sentinel.db
        python3 init_db.py <<< "s"
    else
        echo -e "${GREEN}✅ Usando base de datos existente${NC}"
    fi
else
    python3 init_db.py <<< "s"
fi

echo -e "${GREEN}✅ Base de datos lista${NC}"
echo ""

# =============================================================================
# PASO 4: Verificar configuración
# =============================================================================
echo -e "${YELLOW}⚙️  Paso 4: Verificando configuración...${NC}"

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Archivo .env encontrado${NC}"
    
    # Verificar token de IPinfo
    if grep -q "IPINFO_TOKEN=da3ba9c873020c" .env; then
        echo -e "${GREEN}✅ Token de IPinfo configurado${NC}"
    else
        echo -e "${YELLOW}⚠️  Verifica tu token de IPinfo en .env${NC}"
    fi
else
    echo -e "${RED}❌ Archivo .env no encontrado${NC}"
    echo -e "${YELLOW}📝 Creando desde ejemplo...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Por favor edita .env con tu configuración${NC}"
    exit 1
fi

echo ""

# =============================================================================
# PASO 5: Detener instancia anterior si existe
# =============================================================================
echo -e "${YELLOW}🛑 Paso 5: Deteniendo instancias anteriores...${NC}"

pm2 delete sentinel-geo 2>/dev/null || true
sleep 2

echo -e "${GREEN}✅ Limpieza completada${NC}"
echo ""

# =============================================================================
# PASO 6: Iniciar con PM2
# =============================================================================
echo -e "${YELLOW}🚀 Paso 6: Iniciando servicio con PM2...${NC}"

pm2 start ecosystem.config.js

echo ""
echo -e "${GREEN}✅ Servicio iniciado${NC}"
echo ""

# =============================================================================
# PASO 7: Configurar PM2 para inicio automático
# =============================================================================
echo -e "${YELLOW}⚡ Paso 7: Configurando inicio automático...${NC}"

pm2 save --force
pm2 startup | tail -n 1

echo -e "${GREEN}✅ Configuración guardada${NC}"
echo ""

# =============================================================================
# PASO 8: Verificar estado
# =============================================================================
echo -e "${YELLOW}🔍 Paso 8: Verificando estado del servicio...${NC}"
echo ""

sleep 3
pm2 status sentinel-geo

echo ""

# Verificar que responde
if curl -s http://localhost:8080/health > /dev/null; then
    echo -e "${GREEN}✅ Servicio respondiendo correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Esperando inicialización...${NC}"
    sleep 5
    if curl -s http://localhost:8080/health > /dev/null; then
        echo -e "${GREEN}✅ Servicio respondiendo correctamente${NC}"
    else
        echo -e "${RED}❌ El servicio no responde. Revisa los logs:${NC}"
        echo "   pm2 logs sentinel-geo"
    fi
fi

echo ""

# =============================================================================
# RESUMEN
# =============================================================================
echo "🎉 =========================================================="
echo "🎉  DESPLIEGUE COMPLETADO EXITOSAMENTE"
echo "🎉 =========================================================="
echo ""
echo -e "${GREEN}📍 URLs del servicio:${NC}"
echo ""
echo -e "${YELLOW}🔗 Endpoint de captura (para tu jefe):${NC}"
echo "   http://srv1459428.hostinger.com:8080/view-isologo"
echo ""
echo -e "${YELLOW}📊 Panel de resultados (para ti):${NC}"
echo "   http://srv1459428.hostinger.com:8080/get-test-results"
echo ""
echo -e "${YELLOW}💓 Health check:${NC}"
echo "   http://srv1459428.hostinger.com:8080/health"
echo ""
echo -e "${GREEN}🛠️  Comandos útiles:${NC}"
echo "   pm2 status              - Ver estado"
echo "   pm2 logs sentinel-geo   - Ver logs en tiempo real"
echo "   pm2 restart sentinel-geo - Reiniciar servicio"
echo "   pm2 stop sentinel-geo    - Detener servicio"
echo ""
echo -e "${GREEN}💡 Mensaje sugerido para tu jefe:${NC}"
echo "   'Ingeniero, le comparto el enlace al isologo actualizado"
echo "    para validación: http://srv1459428.hostinger.com:8080/view-isologo'"
echo ""
echo "🚀 =========================================================="
