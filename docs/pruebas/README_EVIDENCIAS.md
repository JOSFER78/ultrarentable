# 📦 PAQUETE DE EVIDENCIA TÉCNICA "ZERO-TRUST" (Ultrarentable)

**Fecha de Generación:** 2026-08-15  
**Ubicación:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/pruebas`  
**Doctrina:** `REAL-ONLY` (Verificación determinista céntimo a céntimo desde base de datos SQLite)

---

## 📑 Contenido del Paquete

Este paquete contiene la documentación forense, cédulas digitales y scripts de reproducción determinista para **6 estrategias verificadas**:

### 🏆 Grupo A: Top 3 "Ultra Rentables" (Alto Retorno / Ratio)
1. **`strat_1_0_23` (Strategy 1.0.23 Sharpe 4.46):**
   - Cédula: [`strat_1_0_23_cedula.json`](strat_1_0_23_cedula.json)
   - Script Replay: [`replay_strat_1_0_23.py`](replay_strat_1_0_23.py)
   - Gráfico: [`strat_1_0_23_equity_drawdown.png`](strat_1_0_23_equity_drawdown.png)
2. **`strat_1_4_140` (Strategy 1.4.140 Dual-Pass OOS):**
   - Cédula: [`strat_1_4_140_cedula.json`](strat_1_4_140_cedula.json)
   - Script Replay: [`replay_strat_1_4_140.py`](replay_strat_1_4_140.py)
   - Gráfico: [`strat_1_4_140_equity_drawdown.png`](strat_1_4_140_equity_drawdown.png)
3. **`strat_1_4_181` (Strategy 1.4.181 High Win Rate):**
   - Cédula: [`strat_1_4_181_cedula.json`](strat_1_4_181_cedula.json)
   - Script Replay: [`replay_strat_1_4_181.py`](replay_strat_1_4_181.py)
   - Gráfico: [`strat_1_4_181_equity_drawdown.png`](strat_1_4_181_equity_drawdown.png)

---

### 🛡️ Grupo B: Top 3 "Fondeo Seguro" (Bajo Drawdown / Estabilidad)
4. **`strat_1_4_125` (Strategy 1.4.125 Bajo Drawdown 4.23%):**
   - Cédula: [`strat_1_4_125_cedula.json`](strat_1_4_125_cedula.json)
   - Script Replay: [`replay_strat_1_4_125.py`](replay_strat_1_4_125.py)
   - Gráfico: [`strat_1_4_125_equity_drawdown.png`](strat_1_4_125_equity_drawdown.png)
5. **`strat_1_0_32` (Strategy 1.0.32 Fondeo Conservador 5.35% DD):**
   - Cédula: [`strat_1_0_32_cedula.json`](strat_1_0_32_cedula.json)
   - Script Replay: [`replay_strat_1_0_32.py`](replay_strat_1_0_32.py)
   - Gráfico: [`strat_1_0_32_equity_drawdown.png`](strat_1_0_32_equity_drawdown.png)
6. **`strat_1_0_54` (Strategy 1.0.54 Dual Gain IS+OOS):**
   - Cédula: [`strat_1_0_54_cedula.json`](strat_1_0_54_cedula.json)
   - Script Replay: [`replay_strat_1_0_54.py`](replay_strat_1_0_54.py)
   - Gráfico: [`strat_1_0_54_equity_drawdown.png`](strat_1_0_54_equity_drawdown.png)

---

## 🚀 Cómo Ejecutar los Scripts de Reproducción

Para ejecutar y verificar cualquier replay determinista:

```bash
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/pruebas"
/home/ubuntu/workspace/pro/trading/01\ Ultrarentable/.venv/bin/python replay_strat_1_0_23.py
/home/ubuntu/workspace/pro/trading/01\ Ultrarentable/.venv/bin/python replay_strat_1_4_140.py
/home/ubuntu/workspace/pro/trading/01\ Ultrarentable/.venv/bin/python replay_strat_1_4_125.py
```

---

## 🛡️ Robustez y Stress Test
Consulta [`INFORME_STRESS_TEST.md`](INFORME_STRESS_TEST.md) para ver la degradación de Profit Factor bajo condiciones adversas de mercado.
