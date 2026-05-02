#!/usr/bin/env python3
"""
================================================================================
SENTINEL-GEO v2.0 - Inicialización de Base de Datos SQLite
Crea las tablas necesarias para el microservicio de auditoría con GPS
================================================================================
"""
import sqlite3
import os

DB_NAME = "sentinel.db"

def init_database():
    """Inicializa la base de datos con las tablas requeridas"""
    
    # Eliminar BD existente si existe (para desarrollo)
    if os.path.exists(DB_NAME):
        print(f"⚠️  Base de datos existente encontrada: {DB_NAME}")
        response = input("¿Deseas recrearla? (s/N): ")
        if response.lower() == 's':
            os.remove(DB_NAME)
            print(f"🗑️  Base de datos anterior eliminada")
        else:
            print("✅ Usando base de datos existente")
            return
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla principal de logs de acceso (VERSIÓN 2.0 CON GPS)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            city TEXT,
            region TEXT,
            country TEXT,
            org TEXT,
            isp_type TEXT,
            coordinates TEXT,
            -- NUEVOS CAMPOS GPS v2.0
            gps_lat REAL,
            gps_lon REAL,
            gps_accuracy REAL,
            location_method TEXT DEFAULT 'ip',
            permission_granted BOOLEAN DEFAULT 0,
            gps_timestamp TEXT,
            -- CAMPOS ORIGINALES
            timezone TEXT,
            postal_code TEXT,
            is_vpn BOOLEAN DEFAULT 0,
            is_mobile BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'pending_gps',
            raw_data TEXT,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Índices para búsquedas rápidas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip ON access_logs(ip_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON access_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON access_logs(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_location_method ON access_logs(location_method)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_gps_coords ON access_logs(gps_lat, gps_lon)')
    
    # Tabla de zonas autorizadas (preparada para futuro uso)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS authorized_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_name TEXT NOT NULL,
            state TEXT NOT NULL,
            city TEXT,
            allowed_network_types TEXT DEFAULT 'both',
            is_active BOOLEAN DEFAULT 1,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar datos de ejemplo (para futura implementación de zonas)
    sample_locations = [
        ("Planta Lerma", "México", "Lerma", "both", "Planta principal de manufactura"),
        ("Obra Querétaro", "Querétaro", "Santiago de Querétaro", "fixed", "Proyecto EX-2024-001"),
        ("Oficina Corporativa", "Ciudad de México", "CDMX", "both", "Oficinas administrativas"),
    ]
    
    cursor.executemany('''
        INSERT INTO authorized_locations (site_name, state, city, allowed_network_types, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_locations)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Base de datos '{DB_NAME}' creada exitosamente")
    print(f"📊 Tablas creadas:")
    print(f"   - access_logs (registro de accesos con GPS)")
    print(f"   - authorized_locations (zonas autorizadas)")
    print(f"📍 {len(sample_locations)} ubicaciones de ejemplo cargadas")
    print(f"🆕 Nuevos campos GPS: gps_lat, gps_lon, gps_accuracy, location_method")

if __name__ == "__main__":
    print("🚀 Sentinel-Geo v2.0 - Inicialización de Base de Datos")
    print("=" * 60)
    init_database()
    print("=" * 60)
    print("✨ Listo para usar!")
