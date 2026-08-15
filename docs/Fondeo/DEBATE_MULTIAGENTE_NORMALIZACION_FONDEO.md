# 🏛️ Informe de Debate Multi-Agente: Normalización Metodológica de Empresas de Fondeo

## 📋 Ficha del Debate
* **Fecha:** 2 de Agosto de 2026
* **Tema:** Corrección de la Metodología Comparativa (Eliminación de Mezclas Desalineadas de Cuentas 50K vs 150K + Métricas Normalizadas por $1,000 de Capital / Drawdown)
* **Comité de Agentes:**
  1. **🛡️ Orquestador & Defensor (Orchestrator)**
  2. **🔍 Crítico & Auditor de Riesgos (Critic / Auditor)**
  3. **📊 Investigador & Verificador Empírico (Researcher)**
  4. **⚡ Arquitecto & Diseñador UI (Architect / Designer)**

---

## 🚀 1. Intervenciones del Comité Cuádruple

### 🛡️ Agente 1: Orquestador & Defensor
> *"El objetivo de esta sesión de trabajo es corregir de raíz la falacia comparativa de medir cuentas de distinto tamaño (ej. $50K contra $150K) de forma plana en una misma tabla. Mezclar tamaños sin alinear distorsiona los costes totales y desorienta la selección táctica de cuentas para nuestros bots cuantitativos de StrategyQuant. Debemos acordar la implementación de un filtro estricto por cohorte de tamaño y métricas relativas por cada $1,000 de riesgo."*

### 🔍 Agente 2: Crítico & Auditor de Riesgos
> *"Auditoría detectada: La ordenación plana por coste total absoluto sin filtrar por cohorte mezclaba planes de $150K ($298 coste total) con planes de $50K ($198 coste total) debido a una coincidencia de texto imprecisa (`'150K'.includes('50K')`). Esto provocaba que una cuenta de $150K apareciera al filtrar por $50K. Exijo dos correcciones inmediatas:*
> 1. *Expresiones regulares estrictas con límites de palabra (`/\\b50K\\b/i`) para impedir el solapamiento.*
> 2. *Incorporación de dos métricas financieras de normalización obligatoria:*
>    - **Coste por $1,000 de Target Objetivo:** $\frac{\text{Coste Total Sumado}}{\text{Target USD} / 1000}$
>    - **Coste por $1,000 de Máximo Drawdown:** $\frac{\text{Coste Total Sumado}}{\text{Max Drawdown USD} / 1000}$

### 📊 Agente 3: Investigador & Verificador Empírico
> *"Evidencias de la base de datos real (27 planes indexados):*
> * *En la cohorte estricta de 50K USD:*
>   * **My Funded Futures (MFFU 50K Rapid EOD):** $39.50 eval + $0 activ = **$39.50 total** $\rightarrow$ **$19.75 por $1K Drawdown** ($2,000 DD).
>   * **TradeDay (50K EOD):** $79.00 eval + $0 activ = **$79.00 total** $\rightarrow$ **$39.50 por $1K Drawdown** ($2,000 DD).
>   * **Topstep (50K Express):** $49.00 eval + $149.00 activ = **$198.00 total** $\rightarrow$ **$99.00 por $1K Drawdown** ($2,000 DD).
>   * **Apex (50K Full):** $16.70 eval + $140.00 activ = **$156.70 total** $\rightarrow$ **$62.68 por $1K Drawdown** ($2,500 DD).
> *Al aislar la cohorte de 50K, observamos cuantitativamente que MFFU ofrece una eficiencia 5x superior a Topstep en coste de drawdown inicial.*

### ⚡ Agente 4: Arquitecto & Diseñador UI
> *"Solución visual e interactiva desplegada en `http://localhost:3000/prop-firms`:*
> 1. **Selector de Cohorte de Tamaño por Defecto (`🎯 COHORTE DE TAMAÑO`):** Mantiene seleccionada por defecto la cohorte **50K USD**, evitando mezclas desalineadas.
> 2. **Columna Destacada `Coste / $1K DD`:** Columna púrpura que indica exactamente el precio por cada $1,000 de margen de riesgo.
> 3. **Botón Interactivo `🔄 Actualizar Datos`:** Conectado en vivo mediante petición HTTP `POST` a `http://127.0.0.1:8000/api/v1/prop-firms/refresh-database` con notificación visual al usuario."*

---

## 📊 2. Matriz de Decisiones Acordadas

| Aspecto | Solución Anterior | Solución Acordada en Debate | Estado |
| :--- | :--- | :--- | :--- |
| **Alineación por Cohorte** | Mezcla de 50K y 150K en la misma tabla. | Selector estricto por Cohorte por defecto (50K) con regex `/\b50K\b/i`. | ✅ Implementado |
| **Métrica de Normalización** | Solo Coste Total Absoluto. | Columna `Coste / $1K Drawdown` ($\frac{\text{Coste Total}}{\text{DD}/1000}$). | ✅ Implementado |
| **Refresco en Vivo** | Datos estáticos sin botón. | Botón `🔄 Actualizar Datos` conectado al backend FastAPI. | ✅ Implementado |
