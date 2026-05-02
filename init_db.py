#!/usr/bin/env python3
"""
Sentinel-Geo - Inicialización de Base de Datos SQLite
Crea las tablas necesarias para el microservicio de auditoría
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
    
    # Tabla principal de logs de acceso
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
            timezone TEXT,
            postal_code TEXT,
            is_vpn BOOLEAN DEFAULT 0,
            is_mobile BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'captured',
            raw_data TEXT,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Índices para búsquedas rápidas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ip ON access_logs(ip_address)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON access_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON access_logs(status)')
    
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
    print(f"   - access_logs (registro de accesos)")
    print(f"   - authorized_locations (zonas autorizadas)")
    print(f"📍 {len(sample_locations)} ubicaciones de ejemplo cargadas")

if __name__ == "__main__":
    print("🚀 Sentinel-Geo - Inicialización de Base de Datos")
    print("=" * 50)
    init_database()
    print("=" * 50)
    print("✨ Listo para usar!")
