# MOTIVO DE CUARENTENA — apps/web/lib/prop-firms.ts

**Fecha:** 2026-09-02  
**Agente:** B10 (Ola B, Tarea task_fa065d9c3015 / W5.8)  
**Directivas asociadas:** D7, D6, Criterio REAL-ONLY, Docs 19 UI Spec  

---

## 1. Identificación del artefacto aparcado

- **Fichero original:** `apps/web/lib/prop-firms.ts`
- **Tamaño:** 4.307 LOC (~180 KB)
- **SHA-256:** `6116e97f0f829b3a18a4fa616430297836fbc3191cc23af4ac1e27a7abae7dc2`
- **Destino en cuarentena:** `cuarentena/web_prop_firms_ts_20260902/prop-firms.ts`

---

## 2. Motivo técnico y de producto (Directiva D7)

1. **Catálogo hardcodeado en cliente:** `apps/web/lib/prop-firms.ts` contenía un array en memoria de 70+ cuentas (`ALL_PROP_FIRM_ACCOUNTS`) con 36 propiedades por objeto, completamente desacoplado del backend y sin respaldo de verificación primaria por parámetro.
2. **Contenido comercial no verificado:** Contenía códigos de cupón, enlaces de afiliados, estructuras promocionales y reclamaciones comerciales sin trazabilidad oficial auditable.
3. **Sustitución canónica (D6/D7):** La página `/prop-firms` pasa a consumir directamente el catálogo v2 servido por el backend en `GET /api/v1/prop-firms/v2` (`services/fondeo/catalogo_firmas_v2.py`), donde cada dato individual de riesgo y economía cuenta con un `SourceRef` explícito (`confidence`, `url`, `captured_at`, `note`), mostrando `NO EVIDENCE` en `--text-3` para cualquier campo no verificado.
4. **Preservación:** De acuerdo con la directiva de no destrucción (nunca `rm`), el archivo se aparca íntegro en esta cuarentena con su manifiesto SHA-256 hasta que el orquestador gestione su retiro definitivo en la integración.
