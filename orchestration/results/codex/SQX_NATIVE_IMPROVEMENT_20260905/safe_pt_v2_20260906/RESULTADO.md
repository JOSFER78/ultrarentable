> Seguimiento 07:21 UTC: la prueba posterior con sesión restringida sigue sin permitir promoción. [Resultado y cierre de esta hipótesis](../native_session_v2_20260906_16utc/RESULTADO.md).

# Mejora nativa comprobada; fondeo pendiente

Comprobación: 2026-09-06, 07:11 UTC. VPS 88.99.210.167. Job `22786f4387505a70c5a7e4f82848b0d7e9309273fb13cd4b931b4fb210a59b38`.

Se corrigió la búsqueda de mejora para excluir objetivos de beneficio porcentuales: en la combinación TS/MC, entrada pendiente y protección inicial, esa receta podía calcular el objetivo desde precio cero. Se conserva la protección inicial. La receta v2 quedó desplegada y terminó un ciclo real con Strategy 3.3.135, dos variantes nativas y recálculo comparado contra el original. No se modificó en esta prueba la configuración de los 30 proyectos del generador.

| Resultado nativo | Original | Variante 1 | Variante 2 |
|---|---:|---:|---:|
| Beneficio IS | 24261,77 | 27226,10 | 25858,91 |
| Beneficio OOS de desarrollo | 11555,19 | 12550,18 | 12550,18 |
| Factor de beneficio IS | 1,62 | 1,74 | 1,72 |
| Factor de beneficio OOS | 2,50 | 2,93 | 2,93 |
| Beneficio/caída IS | 5,62 | 6,72 | 6,19 |
| Beneficio/caída OOS | 7,50 | 8,14 | 8,14 |

Ambas variantes superan el criterio de mejora de desarrollo. Ninguna pasa a candidatas para fondeo: la primera presenta 34 operaciones IS y 6 OOS incompatibles con las sesiones regulares evaluadas; la segunda, 33 y 6. El estado es `NEEDS_SESSION_REPAIR`, `funding_verdict=NO_EVALUABLE`, `probada_para_fondeo=false`, sin candidatas remitidas a la siguiente etapa.

Estos resultados proceden de los históricos instalados: no acreditan rentabilidad con datos de futuros. La procedencia de los datos sigue pendiente, el OOS ya se utilizó en desarrollo y faltan reglas completas fechadas, equivalencia intradía, costes, festivos y una prueba final reservada de intentos de 1–5 días. No se puede concluir que una estrategia supere un examen. La siguiente reparación debe cambiar las reglas de sesión y recalcular; no recortar operaciones del resultado anterior.

Verificación: 102 pruebas correctas en 34,551 segundos; 40 archivos archivados verificados por SHA-256; comparación reproducida localmente; `PTPercent=false` confirmado en el proyecto ejecutado. Evidencia en `local_verification.json`, `job.json` y las dos carpetas adjuntas. La evaluación tiene SHA-256 `55f9222b3d2cfb3e9ac90b35656353c2ec5776bdf823d32927284cfa1e97b34c`.

La búsqueda independiente sigue activa: MNQ M5 pasó de 11287 generadas a las 06:59 UTC a 17679 a las 07:09 UTC. Exporta como máximo cinco preseleccionadas por lote; estas cifras de actividad no son estrategias validadas. La mejora exportó únicamente dos variantes. La recuperación completa tras caída continúa sin acreditarse.
