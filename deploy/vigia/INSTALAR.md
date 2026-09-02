# INSTALACION DE VIGIA V0 EN VPS (ORQUESTADOR / SSH)

> **Documento Operativo para el Orquestador.**
> Contiene los comandos exactos y deterministas para instalar, activar y verificar el servicio y timer systemd de Vigía V0 en el servidor remoto (`oracle-vps`).
> **REGLA:** Ninguna instalacion se realiza de forma automatica; se ejecuta unicamente cuando se abra la ventana de autorizacion correspondiente.

---

## 1. Requisitos Previos y Rutas
- **Usuario VPS:** `ubuntu`
- **Raíz del proyecto:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`
- **Entorno Virtual Python:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/.venv`
- **Carpeta de Resultados:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/orchestration/results/vigia`

---

## 2. Comandos de Instalación (Ejecución remota vía SSH por el ORQ)

```bash
# 1. Asegurar que existe el directorio de destino de los informes
mkdir -p "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/orchestration/results/vigia"

# 2. Copiar los ficheros de unit y timer a /etc/systemd/system/
sudo cp "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/deploy/vigia/ultrarentable-vigia.service" /etc/systemd/system/
sudo cp "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/deploy/vigia/ultrarentable-vigia.timer" /etc/systemd/system/

# 3. Ajustar permisos de los ficheros unit
sudo chmod 644 /etc/systemd/system/ultrarentable-vigia.service
sudo chmod 644 /etc/systemd/system/ultrarentable-vigia.timer

# 4. Recargar systemd para registrar las nuevas units
sudo systemctl daemon-reload

# 5. Habilitar y arrancar el timer diario (06:30 UTC)
sudo systemctl enable --now ultrarentable-vigia.timer
```

---

## 3. Comprobación y Verificación Inmediata

```bash
# A. Verificar estado del timer
systemctl status ultrarentable-vigia.timer --no-pager

# B. Ejecutar un pase de prueba manual en seco del servicio
sudo systemctl start ultrarentable-vigia.service

# C. Verificar el estado de ejecucion del servicio
systemctl status ultrarentable-vigia.service --no-pager

# D. Ver logs del journal
journalctl -u ultrarentable-vigia.service -n 30 --no-pager

# E. Comprobar que el informe diario se genero correctamente en disco
ls -la "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/orchestration/results/vigia"
cat "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/orchestration/results/vigia/$(date -u +%Y-%m-%d).md"
```

---

## 4. Desinstalación / Parada (Rollback)

Si fuese necesario retirar el vigía:

```bash
sudo systemctl stop ultrarentable-vigia.timer
sudo systemctl disable ultrarentable-vigia.timer
sudo rm -f /etc/systemd/system/ultrarentable-vigia.service
sudo rm -f /etc/systemd/system/ultrarentable-vigia.timer
sudo systemctl daemon-reload
```
