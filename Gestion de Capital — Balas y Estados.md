---
tipo: sub-nota
categoria: trading
estado: activo
vigencia: actual
estado_conocimiento: diseño_pendiente_de_simulacion
fecha: 2026-08-03
tags:
  - balas
  - bingx
  - estados
  - gestion-capital
  - sub-nota
  - trading
  - ultrarentable
proyecto: 01 Ultrarentable
ficha_maestra: '[[Ultrarentable]]'
subtema: gestion-capital
fecha_creacion: 2026-08-03
---

# 🎯 Gestión de Capital — Balas y Estados

> Modelo de protección progresiva de beneficios para operativas en el exchange **BingX**. Evita devolver ganancias acumuladas.

> [!WARNING]
> Diseño pendiente de simulación y validación. BingX es un punto de partida del MVP, no el límite definitivo del motor extremo. Ver [[Funcionamiento de Ultrarentable]].

---

## 🎯 Navegación y Enlaces Bidireccionales
- 📌 **Ficha Maestra:** [[Ultrarentable]]
- 🔗 **Sub-notas Relacionadas:** [[Plan 10 Fases]] | [[Dashboard Web]]

---

## Los 6 Estados de una Bala (Posición)

```text
INICIO → CONFIRMACIÓN → CRECIMIENTO → COSECHA → PROTECCIÓN → CIERRE
```

1. **INICIO:** Tamaño base de bajo riesgo.
2. **CONFIRMACIÓN:** Aumento progresivo de posición tras beneficio flotante.
3. **CRECIMIENTO:** Interés compuesto sobre ganancias acumuladas.
4. **COSECHA:** Segregación física e intocable de beneficios fuera del riesgo.
5. **PROTECCIÓN:** Reducción automática de exposición ante debilidad.
6. **CIERRE:** Parada de emergencia antes del límite de drawdown.

**Regla de oro:** El dinero cosechado es intocable y no vuelve al margen operativo.
