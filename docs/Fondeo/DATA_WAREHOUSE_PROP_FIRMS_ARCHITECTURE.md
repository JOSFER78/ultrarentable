# 🏛️ Arquitectura del Almacén de Datos y Matriz Visual de Empresas de Fondeo

## 📋 Resumen del Proyecto

Este documento define la arquitectura técnica integral de datos para el módulo de **Empresas de Fondeo (Prop Firms)** de la plataforma **Ultra Rentable**. Combina una **estructura relacional de Almacén de Datos (Data Warehouse)** con una **interfaz web interactiva de alta densidad analítica**.

---

## 🗄️ 1. Diseño del Almacén de Datos (Data Warehouse Schema)

Para garantizar la integridad, escalabilidad e independencia entre ofertas comerciales, reglas técnicas y modelos de precios, el almacén de datos sigue un modelo relacional normalizado de 4 entidades principales:

```mermaid
erDiagram
    PROP_FIRMS ||--|{ PROP_FIRM_PLANS : offers
    PROP_FIRM_PLANS ||--|| PLAN_PRICING : has
    PROP_FIRMS ||--|| TECHNICAL_RULES : enforces
    PROP_FIRMS ||--|| PAYOUT_POLICIES : specifies

    PROP_FIRMS {
        string id PK
        string name
        int score
        string grade
        int tier
        string website_url
        boolean bot_sqx_compatible
        boolean eod_drawdown_available
    }

    PROP_FIRM_PLANS {
        string id PK
        string firm_id FK
        string account_size
        int account_size_usd
        float target_usd
        float max_drawdown_usd
        string drawdown_type
        string max_contracts
        int min_trading_days
    }

    PLAN_PRICING {
        string plan_id PK, FK
        float base_price_usd
        float promo_price_usd
        float activation_fee_usd
        float sum_effective_cost_usd GENERATED
        string promo_code
    }

    TECHNICAL_RULES {
        string firm_id PK, FK
        string consistency_rule
        string news_policy
        string copy_policy
        string bot_vps_policy
        string_array platforms_supported
    }
```

### 💬 Definición DDL en SQL (PostgreSQL / Supabase)

```sql
-- 1. Tabla de Firmas de Fondeo
CREATE TABLE prop_firms (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    score INT CHECK (score BETWEEN 0 AND 100),
    grade VARCHAR(8) NOT NULL,
    tier INT DEFAULT 2,
    website_url TEXT NOT NULL,
    official_rules_url TEXT NOT NULL,
    bot_sqx_compatible BOOLEAN DEFAULT FALSE,
    bot_policy_summary TEXT,
    eod_drawdown_available BOOLEAN DEFAULT FALSE,
    split_pct VARCHAR(64) NOT NULL,
    last_verified DATE DEFAULT CURRENT_DATE
);

-- 2. Tabla de Planes de Evaluación por Firma
CREATE TABLE prop_firm_plans (
    id VARCHAR(128) PRIMARY KEY,
    firm_id VARCHAR(64) REFERENCES prop_firms(id) ON DELETE CASCADE,
    account_size VARCHAR(64) NOT NULL,
    account_size_usd INT NOT NULL,
    target_usd NUMERIC(12,2) NOT NULL,
    max_drawdown_usd NUMERIC(12,2) NOT NULL,
    drawdown_type VARCHAR(32) NOT NULL CHECK (drawdown_type IN ('EOD', 'TRAILING_INTRADAY', 'MAXIMUM_LOSS')),
    max_contracts VARCHAR(64) NOT NULL,
    min_trading_days INT DEFAULT 0
);

-- 3. Tabla de Precios y Suma del Coste Efectivo
CREATE TABLE plan_pricing (
    plan_id VARCHAR(128) PRIMARY KEY REFERENCES prop_firm_plans(id) ON DELETE CASCADE,
    base_price_usd NUMERIC(10,2) NOT NULL,
    promo_price_usd NUMERIC(10,2),
    activation_fee_usd NUMERIC(10,2) DEFAULT 0.00,
    -- Campo calculado de SUMA EXPLÍCITA: (precio_eval + tarifa_activacion)
    sum_effective_cost_usd NUMERIC(10,2) GENERATED ALWAYS AS (
        COALESCE(promo_price_usd, base_price_usd) + COALESCE(activation_fee_usd, 0.00)
    ) STORED,
    promo_code VARCHAR(64)
);

-- 4. Vista Analítica de Alta Densidad para Indexación
CREATE VIEW view_prop_firm_analytics AS
SELECT 
    f.id AS firm_id,
    f.name AS firm_name,
    f.score,
    f.grade,
    f.tier,
    f.bot_sqx_compatible,
    p.id AS plan_id,
    p.account_size,
    p.account_size_usd,
    pr.base_price_usd,
    pr.promo_price_usd,
    COALESCE(pr.promo_price_usd, pr.base_price_usd) AS current_eval_price,
    pr.activation_fee_usd,
    pr.sum_effective_cost_usd AS coste_total_sumado,
    p.target_usd,
    p.max_drawdown_usd,
    ROUND((p.target_usd / NULLIF(p.max_drawdown_usd, 0)), 2) AS target_loss_ratio,
    p.drawdown_type,
    p.min_trading_days,
    pr.promo_code
FROM prop_firms f
JOIN prop_firm_plans p ON f.id = p.firm_id
JOIN plan_pricing pr ON p.id = pr.plan_id;
```

---

## 🚀 2. Mejoras Implementadas en la Interfaz Web Interactiva

La aplicación web en **`http://localhost:3000/prop-firms`** ha sido completamente actualizada con las siguientes capacidades:

### 📈 Precios Separados y Suma Explícita Destacada
1. **Precio Prueba (Eval):** Muestra el precio regular tachado y el precio promocional en verde (ej. `$39.50`).
2. **Cuota Activación:** Muestra la tarifa única de activación o destaca en verde `$0.00 (Gratis)`.
3. **SUMA COSTETOTAL (Columna Destacada):** Columna resaltada en azul neón con el cálculo exacto de la suma:
   $$\text{Coste Total Sumado} = \text{Precio Eval} + \text{Cuota Activación}$$

### ⚡ Ordenación en 1 Clic por Cualquier Columna
Permite ordenar en sentido **Ascendente (▲)** o **Descendente (▼)** por:
* **SUMA COSTETOTAL** (Para encontrar la oferta económica global más rentable)
* **Precio Prueba (Eval)**
* **Cuota Activación**
* **Ratio Obj/Loss** ($\frac{\text{Target}}{\text{Max Drawdown}}$)
* **Score / Puntuación de la Firma** (0-100 pts)
* **Nombre de la Firma**
* **Tamaño USD de la Cuenta**
* **Días Mínimos de Trading**

### 📥 Exportación Multiformato en 1 Clic
* **Boton `📥 CSV`**: Exporta los datos filtrados en la tabla a un archivo `.csv` listo para Excel / Google Sheets.
* **Boton `📄 JSON`**: Exporta la matriz normalizada en formato `.json` para consumo algorítmico.

---

## 📊 Cobertura Ampliada de Cuentas Indexadas

Se han incorporado **27 planes de cuenta** repartidos entre **9 empresas prioritarias**:

1. **Topstep:** 50K Express, 100K Express, 150K Express.
2. **My Funded Futures (MFFU):** 50K Rapid EOD, 100K Rapid EOD, 150K Rapid EOD, 50K Core Intraday.
3. **Apex Trader Funding:** 25K Full, 50K Full, 100K Full, 150K Full, 300K Full.
4. **TradeDay:** 25K EOD, 50K EOD, 100K EOD, 150K EOD.
5. **Tradeify:** 50K Growth, 50K Select EOD, 100K Select EOD, 150K Select EOD.
6. **Take Profit Trader:** 25K Test EOD, 50K Test EOD, 100K Test EOD, 150K Test EOD.
7. **Bulenox:** 25K Option 1, 50K Option 1, 100K Option 1.
8. **Earn2Trade:** 25K Gauntlet Mini, 50K Gauntlet Mini, 100K Gauntlet Mini.
9. **FundedNext Futures:** 50K Rapid Pro.
