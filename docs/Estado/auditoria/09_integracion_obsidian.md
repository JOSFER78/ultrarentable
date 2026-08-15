# 09. Integración y Convenciones del Vault de Obsidian — Ultrarentable

**Fecha:** 2026-08-09  
**Proyecto:** 01 Ultrarentable  
**Ubicación VPS:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/Estado/auditoria/09_integracion_obsidian.md`  
**Ubicación Vault PC:** `C:\Obsidian\proyectos\trading\01 Ultrarentable\Estado\auditoria\09_integracion_obsidian.md`  
**Estado de Conexión:** 🟢 REST API Viva vía Tailscale (`http://100.106.212.23:27123`)

---

## 1. Diagnóstico de Localización y Estado del Vault

- **Ruta Raíz en Windows (PC):** `C:\Obsidian\`  
- **Ruta Raíz en VPS Linux:** `/home/ubuntu/workspace/pro/`  
- **Mapeo de Rutas Canónico:**  
  - VPS: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/` ↔ PC: `C:\Obsidian\proyectos\trading\01 Ultrarentable`  
- **Conectividad Verificada:**  
  - **Plugin:** Obsidian Local REST API v5.1.0 (Obsidian v1.13.4).  
  - **Puerto HTTP:** 27123 | **Puerto HTTPS:** 27124.  
  - **IP Tailscale:** `100.106.212.23` (Acceso verificado desde el VPS).  
  - **Token de Acceso:** Configurado en `scripts/obsidian_client.py` y `AGENTS.md`.  

---

## 2. Convenciones Reales del Vault de Obsidian

A partir de la inspección directa del vault mediante la API REST, se documentan las convenciones vigentes:

### 2.1 Estructura de Carpetas del Vault
- `/vault/`:
  - `Dashboard.md`: MOC/Panel maestro del sistema completo.
  - `agents.md`: Directivas globales y protocolos de actuación de agentes de IA.
  - `diario/`: Bitácoras diarias (e.g. `_LEEME.md`).
  - `wiki/`: Conceptos transversales e investigaciones (e.g. `Analisis_Conexion_Obsidian.md`).
  - `raw/`: Archivos importados e históricos sin procesar.
  - `proyectos/`:
    - `trading/`:
      - `Trading.md`: Hub/MOC de la categoría Trading.
      - `01 Ultrarentable/`:
        - `Ultrarentable.md`: Ficha maestra del proyecto.
        - `Estado verificado de Ultrarentable.md`: Matriz de hechos comprobados vs no demostrados.
        - `Funcionamiento de Ultrarentable.md`: Teoría operativa, motores económico y fondeo.
        - `Estado/` (contiene `auditoria/` con informes de auditoría).
        - `Fondeo/`
        - `Investigacion/`
        - `Laboratorio/`  

### 2.2 Convenciones de Frontmatter (YAML)
Todas las notas formales en Obsidian incluyen encabezado YAML estructurado según su propósito:
```yaml
---
tipo: proyecto | referencia | hub_categoria | auditoria
categoria: trading
estado: activo | implementacion_parcial_no_certificada | completado
foco_actual: true | false
prioridad: alta | media | baja
metodo_verificacion: inspeccion_local_y_ssh_solo_lectura | test_automatizado
---
```

### 2.3 Wikilinks y Estructura MOC (Map of Content)
- Las notas se interconectan mediante wikilinks directos: `[[Ultrarentable]]`, `[[Trading]]`, `[[Estado verificado de Ultrarentable]]`.
- Cada subcategoría posee un Hub (MOC) que indexa los proyectos activos.
- En la ficha de proyecto (`Ultrarentable.md`), se enlazan jerárquicamente la teoría, el estado verificado y las auditorías.

---

## 3. Estrategia de Integración de `docs/Estado/auditoria/` sin Duplicación

### 3.1 Principio de Única Fuente de Verdad (Single Source of Truth)
- **Teoría, Planes y Decisiones:** La fuente canónica es el Vault de Obsidian (`C:\Obsidian\proyectos\trading\01 Ultrarentable`).
- **Código y Ejecución:** La fuente canónica es el VPS (`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`).
- **Auditorías e Informes de Estado (`docs/Estado/auditoria/`):** Pertenecen al repositorio del VPS como artefactos de ejecución, pero deben ser reflejados automáticamente en Obsidian bajo `/vault/proyectos/trading/01 Ultrarentable/Estado/auditoria/` para consulta y trazabilidad por el usuario.

### 3.2 Protocolo de Sincronización Evitando Duplicados
1. **Acceso REST API (Vía Primaria):**
   - Cuando el PC está encendido y la Local REST API responde en `http://100.106.212.23:27123`, los informes se suben o actualizan directamente vía HTTP `PUT` utilizando el cliente Python `obsidian_client.py` o solicitudes REST directas.
2. **Fallback a Espejo Local VPS (Vía Secundaria):**
   - Si el PC está apagado o fuera de línea, la documentación se guarda localmente en `docs/Estado/auditoria/` del VPS.
   - El script `obsidian_client.py` detecta la desconexión y mantiene la copia local en `docs/`. Al restablecerse la conexión REST API, una sincronización sube las notas pendientes hacia Obsidian.

---

## 4. Clientes y Scripts Disponibles

- **`scripts/obsidian_client.py`** (Ubicación central en `/home/ubuntu/workspace/pro/hermes/01 Gestor Conexión Hermes PC y Obsidian/scripts/obsidian_client.py`):
  - Soporta lectura, búsqueda y escritura en Obsidian a través de la REST API (vía Tailscale IP o localhost SSH).
  - Incluye fallback automático al espejo local `docs/` cuando la API REST no responde.

---

## 5. Vía Recomendada de Integración

**Vía Recomendada:** **API REST de Obsidian sobre Tailscale + Fallback a Espejo Local `docs/`**.
- La API REST en `http://100.106.212.23:27123` está totalmente operativa y permite interactuar directamente con el vault en el PC desde el VPS sin Syncthing.
- Los informes generados en `docs/Estado/auditoria/` se envían al vault mediante solicitudes HTTP REST en la ruta correspondiente `/vault/proyectos/trading/01 Ultrarentable/Estado/auditoria/` conservando la jerarquía y evitando duplicidades.