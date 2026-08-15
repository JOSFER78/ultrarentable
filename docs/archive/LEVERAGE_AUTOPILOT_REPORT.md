# Informe de LeverageAutopilot — Gestión Agresiva y Tiers Reales BingX

## 1. Misión de LeverageAutopilot

Probar de forma totalmente autónoma el apalancamiento más agresivo posible sin exceder los límites ni los tiers de margen de mantenimiento exigidos por el contrato BingX.

## 2. Escalera de Apalancamiento

El explorador de leverage evalúa niveles de apalancamiento escalonados (1×, 5×, 10×, 20×, 50×, 100×, máximo permitido por snapshot):

1. **Consulta de Snapshot**: Se comprueba `InstrumentRuleSnapshotModel` para obtener `max_leverage` y `maintenance_margin_rate`.
2. **Prueba de Resistencia**: Se simulan las variaciones de margen y distancia a liquidación.
3. **Registro de Ensayos**: Cada ensayo se persiste en `leverage_trials` con el apalancamiento, nivel de tier, estado (`PASSED`, `LIQUIDATED`) y capital final alcanzado.
4. **Ganador Seleccionado**: Se selecciona automáticamente el apalancamiento que maximice el capital final sin incurrir en liquidación.
