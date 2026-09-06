# Migración y reanudación comprobadas — 2026-09-06 08:52 UTC

La búsqueda quedó reanudada tras actualizar las configuraciones utilizadas por SQX. El proyecto MCL M1 pasó de 689 a 787 intentos entre las 08:51:51 y las 08:52:43 UTC. Su banco seguía vacío: estos 98 intentos adicionales demuestran actividad, no calidad ni aprobación para fondeo.

Se modificó únicamente PTPercent, de true a false, en Build-Task1.xml de los 30 proyectos canónicos y sus 30 configuraciones de respaldo. SLPercent permanece activo. Se conservaron originales, hashes y bancos en la VPS. El informe registra las 60 modificaciones; dos exportaciones nativas posteriores al arranque, MYM M5 y MGC H4, confirman la configuración cargada. No se ha comprobado mediante exportación nativa individual cada uno de los 30 proyectos.

Se corrigió el indicador de pausa que quedaba persistido cuando la solicitud se retiraba durante un reinicio. Pasaron 17 pruebas del runner, incluidas cuatro específicas de pausa, conservación del trabajo e idempotencia. Solo se reinició el runner para desplegar esa corrección: SQX conservó PID 305818 y el runner adoptó el trabajo vivo sin relanzarlo. El cliente de reinicio agotó su espera de 40 segundos; se comprobó después que el servicio había arrancado, había reconciliado el estado y seguía avanzando. Los cuatro servicios consultados estaban activos.

La comprobación local verifica los informes, las tres configuraciones nativas antes/después, el aumento del contador, el registro de adopción y la coincidencia del hash del runner desplegado. No demuestra recuperación frente a cualquier caída ni una estrategia apta para fondeo.

- [Informe de migración](migration.json).
- [Configuraciones cargadas comprobadas](loaded_verification.json).
- [Primera muestra de reanudación](resume_sample_1.json) y [segunda muestra](resume_sample_2.json).
- [Verificación local](local_verification.json).

Las copias originales permanecen en `/opt/SQX-headless/import/fondeo/pt_migration_20260906/backup/`; la copia del runner previo está en `m1_runner_sqx.py.before_pause_fix`, en el mismo directorio de evidencia remoto. Las estrategias antiguas con PTPercent siguen excluidas del mejorador; esta migración afecta a la configuración de nuevas búsquedas.
