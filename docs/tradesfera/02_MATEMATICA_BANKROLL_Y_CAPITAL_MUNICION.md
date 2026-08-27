---
tipo: tratado-cuantitativo
proyecto: 01 Ultrarentable
sistema: Tradesfera
modulo: 02_MATEMATICA_BANKROLL_Y_CAPITAL_MUNICION
categoria: gestion-de-capital-y-riesgo
estado: activo
vigencia: actual
estado_conocimiento: modelo_matematico_certificado
fecha_creacion: 2026-08-26
tags:
  - tradesfera
  - bankroll
  - capital-municion
  - prop-firms
  - futuros-cme
  - valor-esperado
  - probabilidad-exito
  - tasa-supervivencia
  - amortizacion-cascada
  - kelly-criterion
---

# 🎯 TRATADO MATEMÁTICO: BANKROLL COMO MUNICIÓN Y GESTIÓN DE CAPITAL PARA PROP FIRMS CME
## Modelización Actuarial del Capital de Riesgo, Dinámica de Baterías de Exámenes, Probabilidad Acumulada $P(\ge 1)$, Valor Esperado ($EV$) y Volante de Reinversión Auto-Sostenible

> **Filosofía Tradesfera:** *«Una cuenta de evaluación no es una inversión patrimonial ni un trade individual: es una opción asimétrica barata (un cartucho de munición). El verdadero activo no es la cuenta; el verdadero activo es el Bankroll y la ventaja estadística que lo dispara».*

---

## 🧭 Índice Sistemático

1. [El Paradigma Tradesfera: El Bankroll como Munición](#1-el-paradigma-tradesfera-el-bankroll-como-munición)
2. [Formalización Matemática del Modelo de Munición](#2-formalización-matemática-del-modelo-de-munición)
   - 2.1 [Coste Total Unitario por Cartucho ($C_{\text{total}}$)](#21-coste-total-unitario-por-cartucho-c_texttotal)
   - 2.2 [Capacidad de Disparo: Número de Intentos ($N$)](#22-capacidad-de-disparo-número-de-intentos-n)
   - 2.3 [Probabilidad Acumulada de Cobro: $P(X \ge 1)$ y $P(X \ge k)$](#23-probabilidad-acumulada-de-cobro-px-ge-1-y-px-ge-k)
   - 2.4 [Valor Esperado Matemático del Pool ($EV$) y ROI Teórico](#24-valor-esperado-matemático-del-pool-ev-y-roi-teórico)
   - 2.5 [Tasa de Supervivencia y Probabilidad de Ruina ($P_{\text{ruin}}$)](#25-tasa-de-supervivencia-y-probabilidad-de-ruina-p_textruin)
   - 2.6 [Fraccionamiento por Cestas y Criterio de Kelly Adaptado](#26-fraccionamiento-por-cestas-y-criterio-de-kelly-adaptado)
3. [Ecosistema de Firmas CME y Tablas Numéricas Reales (Precios 2026)](#3-ecosistema-de-firmas-cme-y-tablas-numéricas-reales-precios-2026)
   - 3.1 [Matriz Matricial para Cuentas de \$50,000 USD](#31-matriz-matricial-para-cuentas-de-50000-usd)
   - 3.2 [Matriz Matricial para Cuentas de \$100,000 USD](#32-matriz-matricial-para-cuentas-de-100000-usd)
   - 3.3 [Impacto del Modelo de Activación: \$0 Fee vs Cuota Diferida](#33-impacto-del-modelo-de-activación-0-fee-vs-cuota-diferida)
4. [Simulación de Escenarios y Análisis de Sensibilidad](#4-simulación-de-escenarios-y-análisis-de-sensibilidad)
   - 4.1 [Pool Base de 3.000 € vs 4.000 €: Elasticidad de Supervivencia](#41-pool-base-de-3000--vs-4000--elasticidad-de-supervivencia)
   - 4.2 [Distribución de Rachas Negativas (Streaks de Suspenso)](#42-distribución-de-rachas-negativas-streaks-de-suspenso)
   - 4.3 [Matriz Bidimensional: $p$ vs Payout Promedio ($R_{\text{avg}}$)](#43-matriz-bidimensional-p-vs-payout-promedio-r_textavg)
5. [Modelo de Cascada de Amortización y Reinversión (Flywheel)](#5-modelo-de-cascada-de-amortización-y-reinversión-flywheel)
   - 5.1 [Fase 1: Amortización Acelerada del Principal (Retorno de Inversión)](#51-fase-1-amortización-acelerada-del-principal-retorno-de-inversión)
   - 5.2 [Fase 2: Segregación Ratchet (Bóveda Segura)](#52-fase-2-segregación-ratchet-bóveda-segura)
   - 5.3 [Fase 3: El Volante de Cestas Compuestas (Auto-Sustentabilidad)](#53-fase-3-el-volante-de-cestas-compuestas-auto-sustentabilidad)
6. [Casos Prácticos de Despliegue Operativo](#6-casos-prácticos-de-despliegue-operativo)
   - 6.1 [Caso A: Operativa Masiva de Balas Rápidas (\$0 Fee en MFFU / Tradeify)](#61-caso-a-operativa-masiva-de-balas-rápidas-0-fee-en-mffu--tradeify)
   - 6.2 [Caso B: Operativa Institucional Balanceada en Topstep / TradeDay](#62-caso-b-operativa-institucional-balanceada-en-topstep--tradeday)
   - 6.3 [Caso C: Escalado y Diversificación Multi-Firma (Cesta Sincronizada)](#63-caso-c-escalado-y-diversificación-multi-firma-cesta-sincronizada)
7. [Protocolo de Gestión Psico-Financiera y Reglas Inviolables](#7-protocolo-de-gestión-psico-financiera-y-reglas-inviolables)

---

## 1. El Paradigma Tradesfera: El Bankroll como Munición

En el trading retail tradicional, el operador arriesga su propio balance en una cuenta directa (*brokerage account*). Si posee un capital de $3.500\text{ \euro}$, su pérdida máxima permitida para no arruinar su cuenta suele limitarse al $1\%\text{--}2\%$ por operación ($35\text{ \euro} \text{ a } 70\text{ \euro}$), lo que restringe dramáticamente su apalancamiento efectivo en futuros del CME (donde 1 contrato de ES requiere un colchón sustancial de margen intradía).

La **Filosofía Tradesfera** altera radicalmente esta relación de apalancamiento mediante la **Teoría de Opciones Sintéticas y el Capital de Munición**:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PARADIGMA TRADESFERA: ARQUITECTURA DE MUNICIÓN                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                 ┌───────────────────────────────┐
                                 │   POOL TOTAL DE BANKROLL      │
                                 │      (3.000 € - 4.000 €)      │
                                 │   «El Depósito de Munición»   │
                                 └───────────────┬───────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
        ┌───────────────────────────────┐                 ┌───────────────────────────────┐
        │     CESTA 1 (BATCH DE BALAS)  │                 │    RESERVA INTOCABLE (BUFFER) │
        │   3 a 5 Cuentas Simultáneas   │                 │  Absorción de Varianza Severa │
        │   Coste: ~200 € a 400 €       │                 │  Capital Restante en Espera   │
        └───────────────┬───────────────┘                 └───────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
   [ EVALUACIÓN ]                [ EVALUACIÓN ]
   Pérdida: Coste Unitario       Supera Profit Target
   Riesgo acotado a 1 Bala       Accede a Cuenta Fondeada
   CERO contagio al Bankroll                   │
                                               ▼
                                  ┌───────────────────────────┐
                                  │   FONDEO & COBRO PAYOUT   │
                                  │   Extracción: $1.500 - $4K│
                                  └────────────┬──────────────┘
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
        ┌───────────────────────────────┐             ┌───────────────────────────────┐
        │  AMORTIZACIÓN DEL BANKROLL    │             │   BÓVEDA RATCHET & REINVERSIÓN│
        │  Recuperación del Principal   │             │   Nuevas Cestas Auto-pagadas  │
        └───────────────────────────────┘             └───────────────────────────────┘
```

### Principios Fundamentales del Modelo:
1. **Asimetría Positiva Extrema ($R:R$ Institucional):** 
   Un cartucho de examen cuesta entre $\$39.50$ y $\$198.00\text{ USD}$ (con activación). Al aprobar y alcanzar la fase de pago, el potencial de extracción medio por cuenta oscila entre $\$1,500$ y $\$4,000\text{ USD}$. El ratio beneficio/coste por bala exitosa es de $10:1$ a $40:1$.
2. **Aislamiento Absoluto de la Ruina:**
   Suspender una prueba de fondeo no destruye la equidad de la cuenta de trading; únicamente consume **1 bala** de un cargador de $N$ balas disponibles.
3. **Erradicación de la Falacia del Jugador:**
   Al disponer de un pool de 3.000 € a 4.000 €, el trader no experimenta la presión de «tener que aprobar esta cuenta sí o sí». La probabilidad estadística opera a favor del pool completo a lo largo de una serie suficiente de ensayos independientes.

---

## 2. Formalización Matemática del Modelo de Munición

### 2.1 Coste Total Unitario por Cartucho ($C_{\text{total}}$)

El coste real de un intento no equivale al precio promocional de la prueba. Debe modelarse como la suma estricta de todos los desembolsos requeridos hasta la consecución de la cuenta calificada para cobro:

$$C_{\text{total}} = C_{\text{eval}} + C_{\text{act}} + C_{\text{data}} + C_{\text{reset}}$$

Donde:
- $C_{\text{eval}}$: Coste del examen o suscripción mensual con descuento oficial aplicado ($\text{EUR}$ o $\text{USD}$).
- $C_{\text{act}}$: Cuota de activación obligatoria tras superar el examen (*Pass Fee* / *Activation Fee*). En firmas con $\$0\text{ Fee}$, $C_{\text{act}} = 0$.
- $C_{\text{data}}$: Cuota de data feed mensual en brokers directos (si aplica, habitualmente $\$0$ incluido en plataformas Rithmic/Tradovate de prop firms).
- $C_{\text{reset}}$: Coste de reseteo durante la prueba. En la doctrina Tradesfera, **los resets intra-mes están prohibidos**; se prefiere adquirir una cuenta nueva con cupón promocional si el precio del cupón es menor que el reset. Por tanto, fijamos $C_{\text{reset}} = 0$.

De este modo, para el modelo estándar simplificado:

$$C_{\text{total}} = C_{\text{eval}} + C_{\text{act}}$$

---

### 2.2 Capacidad de Disparo: Número de Intentos ($N$)

Dado un capital líquido total destinado al programa de fondeo ($\text{Bankroll}$, expresado en la misma divisa que el coste o convertido mediante la tasa de cambio $e_{\text{EUR/USD}}$):

$$N = \left\lfloor \frac{\text{Bankroll}}{C_{\text{total}}} \right\rfloor = \left\lfloor \frac{\text{Bankroll}}{C_{\text{eval}} + C_{\text{act}}} \right\rfloor$$

Donde $\lfloor \cdot \rfloor$ denota la función suelo (número entero de balas completas financiables).

> [!NOTE]
> **Ejemplo de Munición Disponible:**
> - Con un Bankroll de $3.500\text{ \euro} \approx \$3.800\text{ USD}$:
>   - En firmas de $\$0\text{ Fee}$ con examen de $\$40\text{ USD}$ (ej. MFFU $50K con cupón `300K`):
>     $$N = \left\lfloor \frac{3800}{40 + 0} \right\rfloor = 95\text{ intentos (balas)}$$
>   - En firmas tradicionales con cuota de activación de $\$149\text{ USD}$ y examen de $\$49\text{ USD}$ (ej. Topstep $50K$):
>     $$N = \left\lfloor \frac{3800}{49 + 149} \right\rfloor = \left\lfloor \frac{3800}{198} \right\rfloor = 19\text{ intentos (balas)}$$

---

### 2.3 Probabilidad Acumulada de Cobro: $P(X \ge 1)$ y $P(X \ge k)$

Sea $p \in (0, 1)$ la **probabilidad combinada de éxito por cartucho individual**, definida como la probabilidad conjunta de:
1. Superar el Profit Target respetando el Max Trailing Drawdown y reglas de consistencia.
2. Superar la fase de colchón de seguridad (*Safety Buffer*) en la cuenta fondeada.
3. Ejecutar con éxito el primer retiro real (*Payout*).

$$p = P(\text{Aprobar Examen}) \times P(\text{Superar Buffer Fondeado}) \times P(\text{Completar Ciclo Retiro})$$

Para un operador algorítmico o discrecional cuantitativo con ventaja estadística demostrada (*edge* certificado), $p$ se sitúa empíricamente entre $0.15$ y $0.35$ ($15\%\text{ a } 35\%$).

#### Probabilidad de Conseguir al Menos 1 Cuenta Cobrando en $N$ Intentos:
Asumiendo independencia estocástica entre los distintos intentos de examen:

$$P(X \ge 1) = 1 - P(X = 0) = 1 - (1 - p)^N$$

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   CURVA DE CONVERGENCIA DE LA PROBABILIDAD ACUMULADA P(X >= 1)                   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
100% ┤                                       ╭─────────────────────────────────────────────────────
 95% ┤                             ╭─────────╯ (Zona de Certeza Estadística: N >= 15 para p=20%)
 90% ┤                       ╭─────╯
 80% ┤                 ╭─────╯
 70% ┤           ╭─────╯
 60% ┤      ╭────╯
 50% ┤  ╭───╯
 30% ┤ ╭╯ (1 intento: p = 20%)
  0% └─┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴───────►
       1     3     5     7     9    11    13    15    17    19    21    23    25    30    40    N (Intentos)
```

#### Generalización para Conseguir al Menos $k$ Cuentas Fondeadas Simultáneas:
Bajo la distribución binomial $X \sim \text{Binomial}(N, p)$:

$$P(X \ge k) = 1 - \sum_{j=0}^{k-1} \binom{N}{j} p^j (1 - p)^{N - j}$$

Donde $\binom{N}{j} = \frac{N!}{j!(N - j)!}$.

---

### 2.4 Valor Esperado Matemático del Pool ($EV$) y ROI Teórico

Sea $R_{\text{avg}}$ el **beneficio neto medio retirado** por cada cuenta que alcanza la fase de pago antes de un eventual breach (promedio de los payouts 1º, 2º, 3º y sucesivos).

El Valor Esperado total del Bankroll ($EV_{\text{pool}}$) tras agotar los $N$ intentos es:

$$EV_{\text{pool}} = \sum_{i=1}^N \mathbb{E}[\text{Retorno Bala}_i] = N \cdot \left[ p \cdot R_{\text{avg}} - C_{\text{total}} \right]$$

Podemos expresar el $EV$ en términos del capital total y del retorno sobre la inversión esperado ($\text{ROI}_{\text{exp}}$):

$$EV_{\text{pool}} = \text{Bankroll} \cdot \left( \frac{p \cdot R_{\text{avg}} - C_{\text{total}}}{C_{\text{total}}} \right) = \text{Bankroll} \cdot \text{ROI}_{\text{unitario}}$$

$$\text{ROI}_{\text{unitario}} = \frac{p \cdot R_{\text{avg}}}{C_{\text{total}}} - 1$$

#### Umbral de Break-Even Probabilístico ($p_{\text{be}}$):
El valor mínimo de probabilidad de éxito por cuenta para no perder dinero en el pool global viene dado por:

$$EV \ge 0 \iff p \cdot R_{\text{avg}} \ge C_{\text{total}} \iff p_{\text{be}} = \frac{C_{\text{total}}}{R_{\text{avg}}}$$

> [!IMPORTANT]
> **Cálculo del Umbral de Rentabilidad ($p_{\text{be}}$):**
> - Si $C_{\text{total}} = \$58.20\text{ USD}$ (Tradeify $50K) y el payout medio retirado es $R_{\text{avg}} = \$2,000\text{ USD}$:
>   $$p_{\text{be}} = \frac{58.20}{2000} = 0.0291 \implies \mathbf{2.91\%}$$
> - ¡Con tan solo un **$3\%$ de probabilidad** de superar la prueba y cobrar, la esperanza matemática del Bankroll es **positiva**!

---

### 2.5 Tasa de Supervivencia y Probabilidad de Ruina ($P_{\text{ruin}}$)

La **Tasa de Ruina Total del Capital** ($P_{\text{ruin}}$) se define como la probabilidad de que los $N$ intentos resulten fallidos consecutivamente, extinguiendo el Bankroll sin haber obtenido ningún payout de retorno:

$$P_{\text{ruin}} = (1 - p)^N$$

La **Tasa de Supervivencia del Capital** ($S_N$) es el complemento directo:

$$S_N = 1 - P_{\text{ruin}} = 1 - (1 - p)^N = P(X \ge 1)$$

Para garantizar que el riesgo de ruina sea estrictamente inferior a un umbral de tolerancia estadística $\alpha$ (por ejemplo, $\alpha = 0.01$, es decir, $99\%$ de supervivencia garantizada):

$$(1 - p)^N \le \alpha \iff N \ge \frac{\ln(\alpha)}{\ln(1 - p)}$$

#### Tabla de Requerimiento de Munición Mínima para Garantizar Supervivencia:

| Probabilidad de Éxito ($p$) | Munición para $S = 90\%$ ($\alpha=0.10$) | Munición para $S = 95\%$ ($\alpha=0.05$) | Munición para $S = 99\%$ ($\alpha=0.01$) | Munición para $S = 99.9\%$ ($\alpha=0.001$) |
|:---:|:---:|:---:|:---:|:---:|
| **$10\%$ (0.10)** | $22\text{ balas}$ | $29\text{ balas}$ | $44\text{ balas}$ | $66\text{ balas}$ |
| **$15\%$ (0.15)** | $15\text{ balas}$ | $19\text{ balas}$ | $29\text{ balas}$ | $43\text{ balas}$ |
| **$20\%$ (0.20)** | $11\text{ balas}$ | $14\text{ balas}$ | $21\text{ balas}$ | $31\text{ balas}$ |
| **$25\%$ (0.25)** | $8\text{ balas}$ | $11\text{ balas}$ | $16\text{ balas}$ | $24\text{ balas}$ |
| **$30\%$ (0.30)** | $7\text{ balas}$ | $9\text{ balas}$ | $13\text{ balas}$ | $20\text{ balas}$ |
| **$40\%$ (0.40)** | $5\text{ balas}$ | $6\text{ balas}$ | $9\text{ balas}$ | $14\text{ balas}$ |

---

### 2.6 Fraccionamiento por Cestas y Criterio de Kelly Adaptado

Disparar todas las balas simultáneamente en un único instante temporal expondría al trader a **riesgo de sincronización de régimen de mercado** (por ejemplo, operar 30 cuentas el mismo día durante un flash crash o un anuncio de tipos de la Fed).

La filosofía Tradesfera impone el despliegue en **Cestas Secuenciales de Cuentas** ($B$, *Batches*):

$$B = \text{Tamaño de Cesta} \in [3, 5]\text{ cuentas simultáneas}$$

$$\text{Número de Ciclos de Disparo} = M = \left\lfloor \frac{N}{B} \right\rfloor$$

#### Fracción de Kelly para Prop Trading de Futuros:
En el marco de Kelly con pago asimétrico $b = \frac{R_{\text{avg}}}{C_{\text{total}}}$ y probabilidad de éxito $p$:

$$f^* = \frac{b \cdot p - (1 - p)}{b} = p - \frac{1 - p}{b} = p - \frac{1 - p}{\frac{R_{\text{avg}}}{C_{\text{total}}}}$$

Dado que $b \gg 10$, el término $\frac{1-p}{b} \approx 0$, lo que implicaría un $f^* \approx p \approx 20\%\text{--}30\%$ del capital total por ciclo. Aplicando la regla de **Fractional Kelly Conservador ($0.25 \times f^*$)** para mitigar la varianza:

$$f_{\text{cesta}} = \frac{1}{4} \cdot f^* \approx 5\%\text{ a } 8\%\text{ del Bankroll total por Cesta}$$

Con un Bankroll de $3.500\text{ \euro}$, cada cesta debe comprometer entre $175\text{ \euro}$ y $280\text{ \euro}$ en costes de evaluación, lo que equivale exactamente a **3–5 cuentas de \$50K en firmas \$0 Fee**.

---

## 3. Ecosistema de Firmas CME y Tablas Numéricas Reales (Precios 2026)

Analizamos el comportamiento de un **Bankroll Fijo de $3.500\text{ \euro}$** ($\approx \$3,800\text{ USD}$ con tipo de cambio medio EUR/USD $= 1.085$) desplegado íntegramente en distintos programas de futuros CME.

---

### 3.1 Matriz Matricial para Cuentas de \$50,000 USD

| # | Firma & Programa | Coste Eval ($C_{\text{eval}}$) | Pass Fee ($C_{\text{act}}$) | Coste Total ($C_{\text{total}}$) | Balas Disponibles ($N$) | $P(X \ge 1)$ ($p=15\%$) | $P(X \ge 1)$ ($p=25\%$) | $P_{\text{ruin}}$ ($p=20\%$) | $EV_{\text{pool}}$ ($R_{\text{avg}}=\$2K, p=20\%$) | ROI Pool ($\%$) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **MyFundedFutures (Rapid)** | **$39.50** | **$0.00** | **$39.50** | **96** | $>99.99\%$ | $>99.99\%$ | $1.4 \times 10^{-9}$ | **+\$34,608** | **+912.8%** |
| 2 | **Tradeify (Growth)** | **$58.20** | **$0.00** | **$58.20** | **65** | $99.99\%$ | $>99.99\%$ | $3.0 \times 10^{-7}$ | **+\$22,217** | **+587.3%** |
| 3 | **TradeDay (Day Trader)** | **$59.00** | **$0.00** | **$59.00** | **64** | $99.99\%$ | $>99.99\%$ | $4.0 \times 10^{-7}$ | **+\$21,824** | **+578.0%** |
| 4 | **FundedNext Futures (Rapid)**| **$99.00** | **$0.00** | **$99.00** | **38** | $99.78\%$ | $>99.99\%$ | $0.01\%$ | **+\$11,438** | **+304.0%** |
| 5 | **BluSky Trading (Static)** | **$110.00** | **$0.00** | **$110.00** | **34** | $99.51\%$ | $>99.99\%$ | $0.05\%$ | **+\$9,860** | **+263.6%** |
| 6 | **Lucid Trading (LucidFlex)** | **$118.30** | **$0.00** | **$118.30** | **32** | $99.30\%$ | $>99.99\%$ | $0.08\%$ | **+\$9,014** | **+238.1%** |
| 7 | **Earn2Trade (TCP 50K)** | **$152.00** | **$0.00** | **$152.00** | **25** | $98.28\%$ | $99.92\%$ | $0.38\%$ | **+\$6,200** | **+163.2%** |
| 8 | **Bulenox (Opción 1)** | **$19.25** | $148.00 | **$167.25** | **22** | $97.19\%$ | $99.76\%$ | $0.74\%$ | **+\$5,120** | **+139.2%** |
| 9 | **Apex Trader Funding (Full)**| **$33.40** | $140.00 | **$173.40** | **21** | $96.50\%$ | $99.68\%$ | $0.92\%$ | **+\$4,758** | **+130.7%** |
| 10 | **Elite Trader Funding** | **$45.00** | $150.00 | **$195.00** | **19** | $95.44\%$ | $99.42\%$ | $1.44\%$ | **+\$3,895** | **+105.1%** |
| 11 | **Topstep (Trading Combine)** | **$49.00** | $149.00 | **$198.00** | **19** | $95.44\%$ | $99.42\%$ | $1.44\%$ | **+\$3,838** | **+102.0%** |
| 12 | **Take Profit Trader (Pro)** | **$85.00** | $130.00 | **$215.00** | **17** | $93.69\%$ | $99.00\%$ | $2.25\%$ | **+\$3,145** | **+86.0%** |
| 13 | **Leeloo Trading (Express)** | **$77.00** | $140.00 | **$217.00** | **17** | $93.69\%$ | $99.00\%$ | $2.25\%$ | **+\$3,111** | **+84.3%** |
| 14 | **TickTick Trader (Direct)** | **$72.50** | $149.00 | **$221.50** | **17** | $93.69\%$ | $99.00\%$ | $2.25\%$ | **+\$3,034** | **+80.6%** |
| 15 | **UProfit Trader (Freedom)** | **$89.00** | $150.00 | **$239.00** | **15** | $91.26\%$ | $98.66\%$ | $3.52\%$ | **+\$2,415** | **+67.4%** |

---

### 3.2 Matriz Matricial para Cuentas de \$100,000 USD

Para cuentas de \$100K, el colchón de pérdida máxima (*Max Drawdown*) suele ser de $\$3,000\text{ a }\$3,500\text{ USD}$, y el payout promedio extraíble aumenta a $R_{\text{avg}} = \$3,500\text{ USD}$.

| # | Firma & Programa | Coste Eval ($C_{\text{eval}}$) | Pass Fee ($C_{\text{act}}$) | Coste Total ($C_{\text{total}}$) | Balas Disponibles ($N$) | $P(X \ge 1)$ ($p=15\%$) | $P(X \ge 1)$ ($p=25\%$) | $P_{\text{ruin}}$ ($p=20\%$) | $EV_{\text{pool}}$ ($R_{\text{avg}}=\$3.5K, p=20\%$) | ROI Pool ($\%$) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | **MyFundedFutures (100K)** | **$75.00** | **$0.00** | **$75.00** | **50** | $99.97\%$ | $>99.99\%$ | $0.001\%$ | **+\$31,250** | **+833.3%** |
| 2 | **Tradeify (100K Growth)** | **$105.00** | **$0.00** | **$105.00** | **36** | $99.70\%$ | $>99.99\%$ | $0.032\%$ | **+\$21,420** | **+566.7%** |
| 3 | **TradeDay (100K Day Trader)**| **$115.00** | **$0.00** | **$115.00** | **33** | $99.45\%$ | $>99.99\%$ | $0.063\%$ | **+\$19,305** | **+508.7%** |
| 4 | **BluSky Trading (100K Static)**| **$190.00** | **$0.00** | **$190.00** | **20** | $96.12\%$ | $99.68\%$ | $1.15\%$ | **+\$10,200** | **+268.4%** |
| 5 | **Bulenox (100K Opción 1)** | **$33.00** | $248.00 | **$281.00** | **13** | $87.91\%$ | $97.62\%$ | $5.50\%$ | **+\$5,447** | **+149.1%** |
| 6 | **Apex Trader Funding (100K)**| **$62.00** | $220.00 | **$282.00** | **13** | $87.91\%$ | $97.62\%$ | $5.50\%$ | **+\$5,434** | **+148.2%** |
| 7 | **Take Profit Trader (100K)** | **$165.00** | $130.00 | **$295.00** | **12** | $85.78\%$ | $96.83\%$ | $6.87\%$ | **+\$4,860** | **+137.3%** |
| 8 | **Topstep (100K Combine)** | **$99.00** | $149.00 | **$248.00** | **15** | $91.26\%$ | $98.66\%$ | $3.52\%$ | **+\$6,780** | **+182.3%** |
| 9 | **UProfit Trader (100K)** | **$150.00** | $150.00 | **$300.00** | **12** | $85.78\%$ | $96.83\%$ | $6.87\%$ | **+\$4,800** | **+133.3%** |

---

### 3.3 Impacto del Modelo de Activación: \$0 Fee vs Cuota Diferida

El análisis cuantitativo revela una divergencia estructural masiva:

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│             COMPARATIVA DE DENSIDAD DE MUNICIÓN: $0 ACTIVATION FEE VS $149 ACTIVATION FEE        │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘

   [ MODELO $0 ACTIVATION FEE (MFFU / Tradeify / TradeDay) ]
   Coste Unitario: ~$40 - $58 USD
   Munición con $3.800 USD: 65 a 96 Balas
   Tasa de Ruina (p=20%): 0.0000003% (PRÁCTICAMENTE NULA)
   Capacidad de Absorber Rachas Negativas: Hasta 40 pérdidas seguidas sin peligro

   [ MODELO TRADICIONAL + PASS FEE $149 (Topstep / Apex / Bulenox) ]
   Coste Unitario: ~$170 - $220 USD
   Munición con $3.800 USD: 17 a 22 Balas
   Tasa de Ruina (p=20%): 0.74% a 2.25% (20,000 VECES MAYOR RIESGO DE RUINA)
   Capacidad de Absorber Rachas Negativas: Máximo 10-12 pérdidas seguidas
```

> [!TIP]
> **Conclusión Táctica Tradesfera:**
> Para la fase de capitalización inicial, el **$100\%$ del Bankroll debe canalizarse a firmas de \$0 Activation Fee**. Esto multiplica la munición disponible por un factor de $\mathbf{3.5\times \text{ a } 4.5\times}$ y reduce la probabilidad de ruina a niveles actuariales despreciables.

---

## 4. Simulación de Escenarios y Análisis de Sensibilidad

### 4.1 Pool Base de 3.000 € vs 4.000 €: Elasticidad de Supervivencia

Analizamos cómo varía la probabilidad de supervivencia $S_N$ y la capacidad de absorber varianza al escalar el Bankroll de $1.000\text{ \euro}$ a $4.000\text{ \euro}$ en cuentas de $\$50\text{K}$ (\$0 Fee, coste medio $\$50\text{ USD}$):

| Bankroll (€) | Bankroll ($ USD) | Balas Disponibles ($N$) | $P(\ge 1)$ ($p=10\%$) | $P(\ge 1)$ ($p=15\%$) | $P(\ge 1)$ ($p=20\%$) | $P(\ge 3\text{ cobros})$ ($p=20\%$) | Varianza Soportada (Max Losing Streak) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1.000 €** | $1,085 | 21 | $89.06\%$ | $96.50\%$ | $99.08\%$ | $82.13\%$ | Hasta 15 fallos |
| **2.000 €** | $2,170 | 43 | $98.88\%$ | $99.90\%$ | $>99.99\%$ | $99.25\%$ | Hasta 28 fallos |
| **3.000 €** | $3,255 | 65 | $99.89\%$ | $>99.99\%$ | $>99.99\%$ | $99.98\%$ | Hasta 42 fallos |
| **4.000 €** | $4,340 | 86 | $99.99\%$ | $>99.99\%$ | $>99.99\%$ | $>99.99\%$ | Hasta 55 fallos |

> [!IMPORTANT]
> **El Rango Óptimo de 3.000 € a 4.000 €:**
> Proporciona entre **65 y 86 intentos**. Incluso con un rendimiento degradado severo ($p = 10\%$, la mitad del rendimiento esperado), la probabilidad de éxito supera el **$99.89\%$**, eliminando completamente el componente de azar en el horizonte temporal anual.

---

### 4.2 Distribución de Rachas Negativas (Streaks de Suspenso)

En un proceso de Bernoulli con $N = 65$ ensayos y $p = 0.20$, la longitud esperada de la racha más larga de pérdidas consecutivas ($\mathbb{E}[L_{\text{max}}]$) se aproxima mediante:

$$\mathbb{E}[L_{\text{max}}] \approx \frac{\ln(N) + \gamma}{\ln(1 / q)} - \frac{1}{2} = \frac{\ln(65) + 0.5772}{\ln(1 / 0.80)} - 0.5 \approx \frac{4.174 + 0.5772}{0.2231} - 0.5 \approx \mathbf{20.8\text{ fallos consecutivos}}$$

Donde $q = 1 - p = 0.80$ y $\gamma \approx 0.5772$ es la constante de Euler-Mascheroni.

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│        DISTRIBUCIÓN DE PROBABILIDAD DE LA PEOR RACHA DE SUSPENSOS EN N=65 INTENTOS (p=0.20)      │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
 Probabilidad
    ▲
 35%│                    ████
 30%│                 ████████
 25%│              ████████████
 20%│           ████████████████
 15%│        ████████████████████
 10%│     ████████████████████████
  5%│  ████████████████████████████  (P(Racha > 30) < 0.1%)
  0%└──┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴────┴───►
       5   10   15   18   20   22   25   28   30   35   40   Longitud de la Racha (Fallos)
```

**Diagnóstico Psicológico:** Un trader con solo 5 o 10 balas entrará en pánico y quebrará ante una racha normal de 12 suspensos consecutivos. El operador de Tradesfera con 65 balas sabe que una racha de 18 a 22 fallos está dentro de la normalidad estocástica ($\pm 1\sigma$) y continúa ejecutando con frialdad matemática.

---

### 4.3 Matriz Bidimensional: $p$ vs Payout Promedio ($R_{\text{avg}}$)

Esperanza matemática neta ($EV_{\text{pool}}$) para un Bankroll de $\$3.800\text{ USD}$ ($N = 65$ balas, $C_{\text{total}} = \$58.20$):

| Probabilidad ($p$) \ $R_{\text{avg}}$ | \$1,000 USD | \$1,500 USD | \$2,000 USD | \$3,000 USD | \$5,000 USD |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **$10\%$ (0.10)** | $+\$2,717$ | $+\$5,967$ | $+\$9,217$ | $+\$15,717$ | $+\$28,717$ |
| **$15\%$ (0.15)** | $+\$5,967$ | $+\$10,842$ | $+\$15,717$ | $+\$25,467$ | $+\$44,967$ |
| **$20\%$ (0.20)** | $+\$9,217$ | $+\$15,717$ | **+\$22,217** | $+\$35,217$ | $+\$61,217$ |
| **$25\%$ (0.25)** | $+\$12,467$ | $+\$20,592$ | $+\$28,717$ | $+\$44,967$ | $+\$77,467$ |
| **$30\%$ (0.30)** | $+\$15,717$ | $+\$25,467$ | $+\$35,217$ | $+\$54,717$ | $+\$93,717$ |
| **$40\%$ (0.40)** | $+\$22,217$ | $+\$35,217$ | $+\$48,217$ | $+\$74,217$ | $+\$126,217$ |

---

## 5. Modelo de Cascada de Amortización y Reinversión (Flywheel)

El capital generado a través de los retiros no se gasta ni se reinvierte caóticamente. Se distribuye a través del **Algoritmo de Cascada en 3 Fases**:

```text
                               ┌───────────────────────────────┐
                               │       PAYOUT BRUTO RECIBIDO   │
                               │        (Ej: $2.500 USD)       │
                               └───────────────┬───────────────┘
                                               │
                                               ▼
                       ┌───────────────────────────────────────────────┐
                       │  ¿Bankroll Inicial (< 3.500 €) Amortizado?    │
                       └───────┬───────────────────────────────┬───────┘
                               │                               │
                          [ NO ]                            [ SÍ ]
                               │                               │
                               ▼                               ▼
                 ┌──────────────────────────┐    ┌──────────────────────────┐
                 │         FASE 1           │    │    FASE 2 & 3: DIVISIÓN  │
                 │   100% RECARGA BANKROLL  │    │   50% / 30% / 20% RATIO  │
                 │   Hasta 3.500 € Íntegros │    └─────────────┬────────────┘
                 └──────────────────────────┘                  │
                                           ┌───────────────────┼───────────────────┐
                                           ▼                   ▼                   ▼
                                ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
                                │ 50% RETIRO REAL  │ │ 30% BÓVEDA RATCHET│ │ 20% MUNICIÓN PRO │
                                │ Cuenta Bancaria  │ │ Reserva Intocable│ │ Nuevas Cestas    │
                                │ Beneficio Neto   │ │ Cripto/Spot USD  │ │ Auto-Financiadas │
                                └──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

### 5.1 Fase 1: Amortización Acelerada del Principal (Retorno de Inversión)

- **Objetivo:** Reducir a CERO el riesgo sobre el patrimonio personal.
- **Regla:** El $100\%$ de los primeros cobros se destinan a reembolsar la cuenta bancaria original hasta reintegrar los $3.000\text{ \euro} \text{ a } 4.000\text{ \euro}$ iniciales.
- **Hito de Riesgo Cero:** En cuanto se cobra el primer o segundo payout acumulado ($\sim \$3,800\text{ USD}$ netos), el sistema pasa a ser **estadísticamente inmune a la quiebra** (*House Money* puro).

---

### 5.2 Fase 2: Segregación Ratchet (Bóveda Segura)

Una vez amortizado el principal, cada nuevo payout recibido ($P_{\text{net}}$) se segrega de forma determinista:

$$\text{Retiro Patrimonial} = 0.50 \times P_{\text{net}} \quad (\text{Transferencia directa a cuenta personal / ahorro})$$

$$\text{Bóveda Ratchet} = 0.30 \times P_{\text{net}} \quad (\text{Capital intocable en stablecoins/cuenta refugio})$$

$$\text{Fondo de Munición} = 0.20 \times P_{\text{net}} \quad (\text{Presupuesto para nuevas cestas de evaluación})$$

---

### 5.3 Fase 3: El Volante de Cestas Compuestas (Auto-Sustentabilidad)

Con solo un $20\%$ de cada payout de $\$2,500\text{ USD}$ ($\$500\text{ USD}$), el sistema financia de forma automática:
- **10 nuevas cuentas de \$50K** en MFFU (\$39.50) o **8 cuentas de \$50K** en Tradeify (\$58.20).
- Estas nuevas 10 cuentas generan una expectativa matemática de $10 \times 0.20 = 2\text{ nuevas cuentas fondeadas}$.
- Esas 2 nuevas cuentas generan $\$4,000\text{ a }\$5,000\text{ USD}$ en nuevos payouts, retroalimentando el bucle de manera perpetua e infinita sin volver a inyectar un solo euro del bolsillo del operador.

---

## 6. Casos Prácticos de Despliegue Operativo

### 6.1 Caso A: Operativa Masiva de Balas Rápidas (\$0 Fee en MFFU / Tradeify)

- **Capital Inicial:** $3.500\text{ \euro}$ ($\approx \$3,800\text{ USD}$).
- **Estrategia de Selección:** 100% Cuentas \$50K en MyFundedFutures Rapid (Cupón `300K`, $\$39.50$) y Tradeify Growth (Cupón `TNT`, $\$58.20$). Coste ponderado: $\$48.85\text{ USD}$.
- **Munición Total:** $N = \lfloor 3800 / 48.85 \rfloor = 77\text{ balas}$.
- **Estructura de Disparo:** 15 Cestas secuenciales de 5 cuentas cada una.
- **Rendimiento Hipotético Conservador ($p = 18\%$):**
  - Cuentas aprobadas y cobradas: $77 \times 0.18 \approx 13.8 \approx 14\text{ cuentas}$.
  - Payout medio por cuenta: $\$1,800\text{ USD}$.
  - Retiro Bruto Total: $14 \times \$1,800 = \$25,200\text{ USD}$.
  - Coste de Munición Incurrido: $77 \times \$48.85 = \$3,761.45\text{ USD}$.
  - **Beneficio Neto:** $\mathbf{+\$21,438.55\text{ USD}}$ ($\approx +20,000\text{ \euro}$ netos).
  - **ROI sobre Bankroll:** $\mathbf{+570\%}$.

---

### 6.2 Caso B: Operativa Institucional Balanceada en Topstep / TradeDay

- **Capital Inicial:** $3.500\text{ \euro}$ ($\approx \$3,800\text{ USD}$).
- **Estrategia de Selección:** Cuentas \$50K combinadas en TradeDay (\$59 total) y Topstep (\$49 eval + \$149 activation fee = \$198 total). Coste medio: $\$128.50\text{ USD}$.
- **Munición Total:** $N = \lfloor 3800 / 128.50 \rfloor = 29\text{ balas}$.
- **Estructura de Disparo:** 6 Cestas de 4–5 cuentas.
- **Rendimiento Hipotético ($p = 22\%$):**
  - Cuentas aprobadas y cobradas: $29 \times 0.22 \approx 6.38 \approx 6\text{ cuentas}$.
  - Payout medio por cuenta (mayor retención en live): $\$2,600\text{ USD}$.
  - Retiro Bruto Total: $6 \times \$2,600 = \$15,600\text{ USD}$.
  - Coste de Munición Incurrido: $29 \times \$128.50 = \$3,726.50\text{ USD}$.
  - **Beneficio Neto:** $\mathbf{+\$11,873.50\text{ USD}}$.
  - **ROI sobre Bankroll:** $\mathbf{+318\%}$.

---

### 6.3 Caso C: Escalado y Diversificación Multi-Firma (Cesta Sincronizada)

Para operadores que emplean **Trade Copiers** (Rithmic Bridge / Tradovate Replicator):

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                   ARQUITECTURA DE CESTA SINCRONIZADA MULTI-PROVEEDOR                             │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                   ┌───────────────────────────┐
                                   │    MASTER ORDER ROUTER    │
                                   │  (NinjaTrader 8 / Sierra) │
                                   └─────────────┬─────────────┘
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
        ┌─────────────────────┐       ┌─────────────────────┐       ┌─────────────────────┐
        │  MFFU Rapid $50K    │       │ Tradeify Growth $50K│       │  TradeDay 50K       │
        │  (2 Cuentas)        │       │ (2 Cuentas)         │       │  (1 Cuenta)         │
        │  Coste: $79.00 USD  │       │ Coste: $116.40 USD  │       │  Coste: $59.00 USD  │
        └─────────────────────┘       └─────────────────────┘       └─────────────────────┘
                   │                             │                             │
                   └─────────────────────────────┼─────────────────────────────┘
                                                 ▼
                                     ┌──────────────────────┐
                                     │ COSTE TOTAL CESTA:   │
                                     │     $254.40 USD      │
                                     │ (6.7% del Bankroll)  │
                                     └──────────────────────┘
```

**Ventajas de la Cesta Multi-Firma:**
1. **Mitigación de Riesgo de Broker/Servidor:** Si un servidor de Rithmic sufre lag, las cuentas de Tradovate no se ven afectadas.
2. **Diversificación de Políticas de Retiro:** Se combinan pagos diarios (TradeDay), on-demand 24h (MFFU) y transferencias ACH/Crypto.
3. **Escalado de Volumen:** Un solo trade ganador de 10 puntos en el NQ ($200 por contrato) genera $\$1,000\text{ USD}$ repartidos entre las 5 cuentas ($200 \times 5$).

---

## 7. Protocolo de Gestión Psico-Financiera y Reglas Inviolables

> [!CAUTION]
> ### 🛑 Las 7 Reglas Cardinales de la Munición en Tradesfera
>
> 1. **Prohibición de Over-Leveraging por Desesperación:** Jamás aumente el número de contratos tras perder una cuenta de examen. La cuenta se suspende, se anota el fallo en el log forense y se pasa a la siguiente bala con el tamaño de lote programado.
> 2. **Prohibición de Resets Costosos:** Si un reset cuesta $\$80$ y una cuenta nueva con código promocional cuesta $\$39.50$, **siempre adquiera una cuenta nueva**. No pague sobrecostes a las firmas.
> 3. **Respeto del Límite de Cesta:** Jamás ejecute más del $10\%$ del Bankroll total en un mismo día o evento macroeconómico.
> 4. **No-Contagio de Margen:** Una cuenta en pérdida no debe «salvarse» cerrando coberturas o alterando otras cuentas de la cesta. Cada bala vive y muere en aislamiento.
> 5. **Extracción Obligatoria al Alcanzar el Colchón:** Tan pronto como el balance supere el *Safety Threshold* ($+\$2,100\text{ a }+\$2,600$), solicite inmediatamente el retiro máximo permitido. No acumule saldo en una prop firm más allá de lo necesario.
> 6. **Registro Imparcial de la Tasa $p$:** Calcule su tasa real $p$ cada 20 intentos con datos auditados. Si su tasa $p$ cae por debajo del $8\%$, detenga el disparo de munición y regrese al motor cuantitativo en backtest/incubación para re-optimizar sus sistemas.
> 7. **Protección Ratchet Fuerte:** El dinero que ingresa en la Bóveda Segura jamás vuelve al cargador de balas para «recuperar rachas». El volante debe girar únicamente con el $20\%$ asignado.

---

## 📚 Documentos y Herramientas Relacionadas

- 📑 **Catálogo Vivo de Firmas:** `Investigacion/03_CATALOGO_MAESTRO_34_PROP_FIRMS.md`
- 🤖 **Especificación de Futuros CME:** `Investigacion/04_SISTEMA_MUNDIAL_PROP_FIRMS_FUTUROS.md`
- 🛡️ **Doctrina Dual y Balas Ultra:** `Investigacion/02_ARQUITECTURA_Y_EVOLUCION_ULTRARENTABLE_2026.md`
- 🌐 **Calculadora Web Interactiva de ROI:** `http://localhost:3000/prop-firms` (`ExtractionRoiCalculator.tsx`)
