---
id: REGLAS
titulo: "Reglas invariantes"
estado: VIGENTE
actualizado: "2026-08-31"
---

# REGLAS INVARIANTES

1. **REAL-ONLY.** Cero datos inventados. Sin dato ⇒ `NO DATA`/`ERROR`, nunca un valor por defecto.
2. **Nunca `rm`.** Todo lo retirado va a `cuarentena/` con manifiesto SHA-256.
3. **Se trabaja en la carpeta, no en GitHub.** Nada se sube sin orden expresa (decisión #23).
4. **Nada valioso vive solo en RAM.** Toda población se persiste a disco y BD inmediatamente.
5. **El objetivo no autoriza a maquillar.** Si el número real es peor que la meta, se reporta el
   número real.
6. **Regla #26 (doctrina):** cualquier cambio que altere qué operaciones produce el motor sube
   `CURRENT_ENGINE_VERSION`; toda certificación con versión anterior pasa a `LEGACY_MOTOR_<motivo>`
   y deja de contar como aprobada. Nunca se borra.
