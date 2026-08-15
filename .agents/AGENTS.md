# DIRECTIVA MAESTRA AUTOMÁTICA PARA TODOS LOS AGENTES DE IA (ANTIGRAVITY / CLAUDE CODE / CODEX / CURSOR)

> **REGLA DE Descubrimiento Automático:** Cualquier agente de IA que inicie sesión en este proyecto debe acatar esta directiva de forma transparente y sin necesidad de que el usuario vuelva a explicar el plan.

---

## 1. FUENTE ÚNICA DE VERDAD (OBSIDIAN)
- **Ruta de Obsidian:** `C:\Obsidian\proyectos\trading\01 Ultrarentable`
- **Ruta en VPS Linux:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`
- **Documento Maestro:** `docs/14_bingx/ESPECIFICACION_COMPLETA_BINGX_ULTRARENTABLE.md` y `docs/09_frontend/WEB_MVP.md`

---

## 2. GUARDARRAÍLES INQUEBRANTABLES PARA LA IA

1. **PROHIBIDO INVENTAR PÁGINAS O VISTAS WEB**:
   - La portada principal (`apps/web/app/page.tsx`) y el menú (`Sidebar.tsx`) solo contendrán las pantallas oficiales establecidas en el plan de Obsidian.
   - NUNCA añadir subpáginas temporales, borradores, ni enlaces a versiones antiguas que saturen o confundan la interfaz.

2. **LECTURA PREVIA OBLIGATORIA DEL PLAN**:
   - Antes de escribir o modificar código en `apps/` o `services/`, el agente debe revisar el plan en Obsidian para saber qué paso o fase está en curso.

3. **MANTENER EL PROYECTO LIMPIO**:
   - No dejar archivos `.zip`, scripts `.bat` sueltos en la raíz ni archivos temporales (`dispatch-state.json`, `__pycache__`).

---

## 3. ESTADO ACTUAL DE LA APLICACIÓN
- **Frontend (Next.js):** Running en `http://localhost:3000/` (`apps/web`).
- **Backend (FastAPI):** Running en `http://127.0.0.1:8000/` (`services/api`).
