# Corrección del motor: objetivos porcentuales iniciales

La prueba nativa controlada del 6 de septiembre confirmó el problema en Strategy 1.18.140: con entrada pendiente, motor Tradestation y UseInitialSLPT activo, el objetivo porcentual inicial se calcula desde precio cero. El código instalado y el recálculo explican los cierres inmediatos. No se ha modificado el código del proveedor.

Al desactivar esa opción únicamente en el experimento, los cortos inmediatos pasaron de 79/79 a 2/77 y desaparecieron los objetivos de beneficio con distancia no positiva. La opción mantiene las protecciones iniciales; desactivarla retrasa SL/PT hasta la siguiente barra, por lo que este cambio NO se aplica en producción. La variante resultó rechazada por regresión en las métricas IS. No acredita fondeo.

El selector del motor ahora excluye las fuentes con esa combinación y registra nombre, hash y motivo. Revisa también las salidas trasplantadas de variantes antes del recálculo. Conserva la búsqueda y los límites de cinco fuentes seleccionadas por lote y dos variantes exportadas. En la inspección real quedaron 19 fuentes excluidas y una admisible: Strategy 3.3.135. El trabajo nativo sobre ella terminó a las 08:51 de Madrid: generó dos variantes, recalculó ambas y el control, y descartó las dos. La primera empeoró las métricas IS; la segunda no alcanzó la mejora mínima del 5 % en el Ret/DD más débil de desarrollo. También se detectaron operaciones incompatibles con la sesión examinada. Ninguna pasó a la siguiente etapa.

Verificación: 100 pruebas de ejecución correctas en 34,708 segundos; los 24 archivos del manifiesto de archivo nativo coinciden por SHA-256. El motor desplegado tiene hash e5ae7381be49f21c6a60f959b77642bd18f0daa112f3aab24122e89cf9351343.

Evidencia: manifest.json, comparison.json, assessment.json, órdenes originales, archivos SQX de entrada y recalculados, archive_verified.json y local_verification.json en esta carpeta.

Sigue faltando una estrategia aceptada y validación de fondeo con datos de futuros acreditados, reglas completas y muestra final reservada. El OOS consultado sirve para desarrollo; no certifica un examen de 1–5 días.

La evidencia del último trabajo está en [recálculo y evaluación](../auto_improvement_a2b595b131a17703fbae/assessment.json) y [búsqueda nativa](../auto_exit_search_a2b595b131a17703fbae/state.json). Sus 40 archivos se verificaron por SHA-256 tras copiarlos localmente.

La búsqueda continua sigue activa y encadena trabajos: terminó MGC M5 seleccionando solo cinco de 3.175 estrategias del banco y comenzó MNQ M5, con 5.492 generadas a las 08:49 de Madrid. Son preselecciones, no estrategias validadas. El temporizador de mejora permanece activo para revisar nuevas fuentes cada hora.
