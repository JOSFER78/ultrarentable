---
id: RIESGOS
titulo: "Lo que puede salir mal (y cómo se detecta)"
estado: VIGENTE
actualizado: "2026-08-31"
---

# LO QUE PUEDE SALIR MAL (y cómo se detecta)

| Riesgo | Cómo se detecta | Qué se hace |
| :--- | :--- | :--- |
| Ninguna base supera el criterio 1.1 | Censo de la Fase 1 | Ampliar la campaña, no relajar el criterio |
| El motor realista mata todas las estrategias | El P&L cae a negativo en Fase 2 | Es la respuesta correcta: eran ilusiones |
| El motor de mejora sobreajusta | El holdout ciego no confirma | La mejora se descarta, se reporta `SIN MEJORA` |
| La envolvente da miles de % con ruina alta | Percentil 5 y prob. de ruina en Fase 5 | Se presentan ambos números, decide el usuario |
| Paper diverge del backtest | Reconciliación de la Fase 8 | Se corrige el modelo de fricción, no el backtest |
| 4 cores no dan abasto | Cola de la Fase 3 se atasca | Reducir matriz o ampliar VPS, decide el usuario |
| Un servicio con código viejo en memoria contamina la BD | Filas con `engine_version` < vigente o `gates_passed=0` en estados APPROVED | Parar/reiniciar el servicio tras cada bump de motor; el censo reclasifica |
