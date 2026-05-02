module.exports = {
  apps: [{
    name: 'sentinel-geo',
    script: 'main.py',
    interpreter: 'python3',
    cwd: '/home/diego-terrazas/sentinel-geo',
    instances: 1,
    exec_mode: 'fork',
    autorestart: true,
    watch: false,
    max_memory_restart: '512M',
    env: {
      NODE_ENV: 'production',
      PORT: 8080
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    kill_timeout: 5000,
    listen_timeout: 10000,
    // Configuración de reinicio
    min_uptime: '10s',
    max_restarts: 10,
    // Configuración de logs
    log_type: 'json',
    // Hooks
    args: []
  }]
};
