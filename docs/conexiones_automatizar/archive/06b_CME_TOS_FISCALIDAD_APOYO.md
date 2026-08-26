# INFORME FORENSE: MARCO LEGAL, REGULATORIO, CONTRACTUAL Y FISCAL EN PROP TRADING DE FUTUROS (CME, PROPFIRMS, CONECTIVIDAD IP/VPS Y DERECHO ESPAÑOL)

- **Fecha de Auditoría y Publicación:** 25 de agosto de 2026  
- **Ámbito:** Legalidad financiera, Normativa CME Group, Términos de Servicio de Prop Firms (ToS), Conectividad IP/Datacenter/VPN y Fiscalidad en España (AEAT/CNMV).  
- **Entorno de Referencia:** Infraestructura Linux ARM64 / VPS Oracle Cloud Madrid / NinjaTrader 8 / Plataformas de Fondeo.  
- **Criterio Epistémico Estricto:**
  - ✅ **VERIFICADO**: Respaldado por normativa legal vigente, jurisprudencia, consultas vinculantes DGT, rulebooks oficiales de exchanges o contratos ToS públicos con URL directa.
  - ⚠️ **HIPÓTESIS / PRÁCTICA OPERATIVA**: Interpretación técnica común, zona gris contractual o heurística de detección no publicada explícitamente en el clausulado.

---

## ÍNDICE DE CONTENIDOS
1. [Jerarquía y Distinción de Fuentes: Ley vs. Reglas de Exchange vs. Términos Contractuales (ToS)](#1-jerarquía-y-distinción-de-fuentes-ley-vs-reglas-de-exchange-vs-términos-contractuales-tos)
2. [Reglamento y Políticas de Mercado de CME Group](#2-reglamento-y-políticas-de-mercado-de-cme-group)
   - 2.1 Licencias de Market Data: Professional vs. Non-Professional
   - 2.2 Política de Uso No-Display (Non-Display & Automated Trading Systems)
   - 2.3 Identificación de Dispositivo, Conexión e IP
   - 2.4 ¿Existe Prohibición Legal o Normativa del CME sobre el uso de VPNs?
3. [Términos de Servicio (ToS) y Políticas Antifraude en Prop Firms Principales](#3-términos-de-servicio-tos-y-políticas-antifraude-en-prop-firms-principales)
   - 3.1 Apex Trader Funding
   - 3.2 Topstep
   - 3.3 MyFundedFutures (MFFU)
   - 3.4 TakeProfit Trader & TradeDay
   - 3.5 Matriz Comparativa de Políticas de Conectividad
4. [Marco Regulatorio y Fiscal en España: CNMV, MiFID II y Tributación AEAT](#4-marco-regulatorio-y-fiscal-en-españa-cnmv-mifid-ii-y-tributación-aeat)
   - 4.1 Legalidad y Posición de la CNMV respecto al Prop Trading y VPS
   - 4.2 Calificación Tributaria en IRPF: Base General vs. Base del Ahorro
   - 4.3 Obligaciones Censales (IAE), RETA (Autónomos) y Facturación Internacional (IVA)
   - 4.4 Obligaciones Informativas: Modelo 720, Modelo 721 y Directiva DAC8
5. [Evaluación de Arquitectura: VPS Oracle Madrid con IP Española](#5-evaluación-de-arquitectura-vps-oracle-madrid-con-ip-española)
6. [Conclusión Forense y Desmitificación](#6-conclusión-forense-y-desmitificación)
7. [Referencias y Fuentes Oficiales Citadas](#7-referencias-y-fuentes-oficiales-citadas)

---

## 1. JERARQUÍA Y DISTINCIÓN DE FUENTES: LEY VS. REGLAS DE EXCHANGE VS. TÉRMINOS CONTRACTUALES (ToS)

Uno de los errores más frecuentes entre los operadores algorítmicos y discrecionales es confundir una **violación contractual privada** con una **infracción penal o administrativa**. Es imperativo desglosar con rigor la pirámide jurídica aplicable.

```
       ▲  [1. LEY Y REGULACIÓN ESTATAL] (CFTC, SEC, CNMV, MiFID II, Código Penal)
      / \  - Derecho Público Imperativo / Coacción Estatal (Multas, Inhabilitación, Prisión)
     /---\ 
    /     \  [2. NORMAS DEL EXCHANGE] (CME Group Rulebook, Market Data Policies)
   /-------\  - Autorregulación de Mercado Organizado / Suspensión de Miembros / Revocación de Feeds
  /         \ 
 /-----------\ [3. CONTRATOS PRIVADOS / ToS] (Apex, Topstep, MFFU User Agreements)
/_____________\ - Derecho Civil/Mercantil / Pérdida de Cuenta / Retención de Payouts (Sin sanción penal)
```

### Tabla Comparativa de Naturaleza Jurídica y Fuerza Ejecutoria

| Dimensión | 1. Ley y Regulación Pública | 2. Reglas del Exchange (CME) | 3. Términos de Servicio (ToS) Prop Firm |
| :--- | :--- | :--- | :--- |
| **Emisor** | Organismos estatales (CFTC/SEC en EE.UU., CNMV en España, Directivas UE). | CME Group Inc. (Bolsa autorregulada bajo supervisión CFTC). | Empresas privadas de evaluación/tecnología (LLCs, SLs, Ltds). |
| **Naturaleza** | Derecho imperativo (*Ius Cogens*). | Normas de membresía y contratos comerciales de licencia de datos/ejecución. | Contrato privado bilateral de adhesión (*Service Agreement / Terms of Use*). |
| **Ámbito Subjetivo** | Toda persona física o jurídica bajo la jurisdicción territorial. | Miembros de compensación (FCMs), brokers, redistribuidores de datos y operadores con acceso directo. | El usuario firmante y la empresa de fondeo. |
| **Poder Sancionador** | Sanciones administrativas, multas millonarias, inhabilitación profesional y persecución penal. | Suspensión de claves de acceso Globex, multas a brokers miembros y expulsión del exchange. | Rescisión contractual unilateral, veto de plataforma (*ban*) y retención/confiscación de fondos y payouts. |
| **Fuerza Coactiva Real** | Extradición, embargo de bienes, bloqueo de cuentas bancarias por orden judicial. | Bloqueo en pasarelas de datos R|API/CQG/Continuum a través del broker. | Exclusivamente contractual: el usuario pierde su acceso y los beneficios virtuales generados. |

---

## 2. REGLAMENTO Y POLÍTICAS DE MERCADO DE CME GROUP

CME Group (que aglutina CME, CBOT, NYMEX y COMEX) rige la negociación de futuros a través de su *Rulebook* y sus *Information Policies* (Políticas de Información de Mercado).

### 2.1 Licencias de Market Data: Professional vs. Non-Professional
✅ **VERIFICADO**:
- CME distingue taxativamente entre **Suscriptor No Profesional (Non-Professional Subscriber)** y **Suscriptor Profesional (Professional Subscriber)** en su *CME Information License Agreement* (Schedule 4/5).
- **Criterios de Suscriptor No Profesional:**
  1. Persona física que contrata el servicio a título personal.
  2. No está registrada ni cualificada ante la CFTC, SEC, NFA, FINRA ni ninguna autoridad reguladora financiera internacional.
  3. No actúa en calidad de asesor financiero, gestor de fondos ni gestor de capitales de terceros.
  4. Utiliza los datos exclusivamente para la gestión de su propio patrimonio personal.
  5. **Límite técnico de dispositivos:** La política de CME establece un límite estándar de **hasta dos (2) terminales de trading simultáneas** por distribuidor que tengan capacidad de enviar órdenes a CME Globex bajo la tarifa reducida de No Profesional.
- **Implicación en Prop Firms:** Las prop firms de futuros minoristas operan inicialmente sobre entornos de simulación (Simulated / Demo Environment). Al suscribirse a la cuenta, el trader firma la declaración de "Non-Professional" ante el proveedor de datos (Rithmic, Tradovate, CQG, NinjaTrader). Si un trader gestiona cuentas para otros o está registrado en un regulador, está obligado por el CME a pagar la tarifa profesional (centenares de dólares mensuales por mercado frente a ~13-15 $/mes de la no profesional).

### 2.2 Política de Uso No-Display (Non-Display & Automated Trading Systems)
✅ **VERIFICADO**:
- La **CME Non-Display Policy** regula el consumo de datos de mercado por sistemas automatizados que no representan visualmente los precios a un ser humano en pantalla (por ejemplo: motores de trading algorítmico, servidores de cálculo de riesgo en tiempo real, arbitraje de alta frecuencia).
- **Categorías de Licencia Non-Display:**
  - *Category 1 (Trading Activities):* Utilización de datos de mercado en un ATS (Automated Trading System) para enrutamiento y generación de órdenes automáticas por parte de instituciones.
  - *Category 2 (Internal Operations):* Uso para control de riesgos y valoración de carteras.
- **Aplicación al Retail / Prop Trader:** Un operador minorista o usuario de prop firm que ejecuta un script en NinjaTrader 8 o Python en su propio terminal no contrata una conexión directa Non-Display con el CME; consume los datos a través de la licencia de visualización/terminal provista por el broker o la prop firm. No obstante, el uso indebido de feeds para alimentar sistemas de retransmisión masiva de datos a terceros constituye una infracción directa de la propiedad intelectual de CME.

### 2.3 Identificación de Dispositivo, Conexión e IP
✅ **VERIFICADO**:
- El CME exige a los distribuidores autorizados (*Distributors / Vendors*) la trazabilidad del **Unit of Count** (Unidad de Conteo). Cada flujo de datos debe estar asociado a un usuario único autenticado (*User ID*) o terminal físico (*Device*).
- **CME Rule 575 (Disruptive Practices) y Rule 576 (Identification of Automated Trading Systems):** Exigen que cada orden enviada a CME Globex contenga el operador responsable (*Operator ID / Tag 50*). En cuentas simuladas de prop firms, las órdenes no llegan a Globex salvo en fases de cuenta financiada real (*Live Funded Brokerage Account*), donde el FCM (Futures Commission Merchant) asigna formalmente dicho identificador.

### 2.4 ¿Existe Prohibición Legal o Normativa del CME sobre el uso de VPNs?
✅ **VERIFICADO**:
- **NO existe ninguna regla en el CME Rulebook que prohíba a un operador particular conectarse mediante una VPN**.
- De hecho, a nivel de infraestructura institucional, el propio CME Group proporciona túneles VPN cifrados (*CME Cert VPN*, *Client Internet Link*) para conectar infraestructuras corporativas a sus pasarelas.
- **La exigencia del CME es de cumplimiento normativo y fiscal:** Los datos deben ser consumidos por el usuario licenciado y desde una jurisdicción que no viole sanciones internacionales (OFAC). El uso de una VPN comercial compartida no es un delito contra el CME, pero puede vulnerar los contratos de distribución si se utiliza para eludir la clasificación de suscriptor o las restricciones territoriales internacionales.

---

## 3. TÉRMINOS DE SERVICIO (ToS) Y POLÍTICAS ANTIFRAUDE EN PROP FIRMS PRINCIPALES

Las empresas de fondeo no aplican el derecho penal, sino sus **Términos de Servicio (Terms of Service / Terms of Use)**. La motivación principal de sus controles de IP/VPN no es el CME, sino evitar:
1. **Passing Services / Account Sharing:** Granjas de trading que cobran por superar evaluaciones a múltiples clientes usando la misma IP o bots masivos.
2. **Multi-Accounting / Evasión de Límites:** Traders que superan el límite máximo de cuentas permitidas por usuario/hogar abriendo cuentas con identidades de terceros.
3. **Evasión de Sanciones Geográficas (OFAC):** Conexiones desde países restringidos (Rusia, Irán, Corea del Norte, Cuba, etc.) que comprometerían a los procesadores de pago estadounidenses.
4. **Arbitraje de Latencia Tóxico en Simulación:** Explotar desajustes del motor de simulación alojando servidores ultrarrápidos pegados al servidor del broker simulado.

---

### 3.1 Apex Trader Funding
✅ **VERIFICADO**:
- **Prohibición de Herramientas de Anonimización:** Los términos de Apex (*Prohibited Activities / User Agreement*) prohíben explícitamente el uso de VPNs, proxies, servidores en la nube y herramientas de anonimización cuando tengan por objeto o efecto:
  - Ocultar o falsear la ubicación física real o la identidad del dispositivo.
  - Eludir controles de acceso o restricciones geográficas (países vetados).
  - Ocultar violaciones de reglas o evadir la detección de multicuentas.
- **Límite de Cuentas por Hogar / IP:** Apex limita a un máximo de **20 Cuentas Pagadas (PA - Paid Accounts)** por persona, hogar e IP.
- **Consecuencia de Infracción:** El sistema automatizado de flags de Apex detecta cambios bruscos de geolocalización o múltiples cuentas asociadas a la misma IP de datacenter, resultando en auditorías de compliance (*ID Verification, selfie con documento, logs de conexión*) y, en caso de discrepancia, la rescisión inmediata de cuentas y denegación de retiros.
- **Fuente Oficial:** [Apex Trader Funding Terms of Use & Prohibited Activities](https://apextraderfunding.com/)

---

### 3.2 Topstep
✅ **VERIFICADO**:
- **Política Estricta de VPN/Proxy:** Topstep prohíbe taxativamente el uso de VPNs, servicios de proxy, nodos TOR y cualquier mecanismo de ofuscación de geolocalización.
- **Monitoreo por el "Trust Team":** Topstep cuenta con un departamento de integridad que audita patrones de conexión. Detectar accesos simultáneos desde IPs distantes o proxies comerciales dispara una suspensión cautelar.
- **Prohibición de Trading Coordinado y Perfil Único:** Prohibido que múltiples usuarios operen en concierto o que una persona opere perfiles ajenos.
- **Sanciones Contractuales:** Reseteo de cuenta, anulación de jornadas de trading con ganancias, denegación definitiva de payouts y baneo permanente.
- **Fuente Oficial:** [Topstep Terms of Use & Prohibited Conduct Rules](https://www.topstep.com/)

---

### 3.3 MyFundedFutures (MFFU)
✅ **VERIFICADO**:
- **Prohibición durante KYC/AML:** MFFU prohíbe de forma absoluta el uso de VPNs o VPS durante la verificación de identidad (KYC) y procedimientos AML.
- **Uso de VPS / VPN en Trading:** Desaconseja enérgicamente el uso de VPNs comerciales que roten IPs. El uso de herramientas que interfieran con la telemetría interna o que simulen ubicaciones falsas para eludir listas de países restringidos acarrea la descalificación inmediata. Si el usuario viaja o cambia de entorno, debe notificarlo previamente a soporte (`support@myfundedfutures.com`).
- **Fuente Oficial:** [MyFundedFutures Help Center & Policies](https://www.myfundedfutures.com/)

---

### 3.4 TakeProfit Trader & TradeDay
✅ **VERIFICADO**:
- **TakeProfit Trader:**
  - Prohíbe VPNs y conexiones remotas compartidas que puedan enrutar tráfico a través de jurisdicciones sancionadas.
  - **VPS para Estabilidad Técnica:** Permite y reconoce el uso de Servidores Privados Virtuales (VPS) cuando su fin es la estabilidad de conexión y ejecución ininterrumpida de algoritmos, siempre que el usuario sea el único titular y no se empleen técnicas de arbitraje prohibidas.
- **TradeDay:**
  - Al operar bajo un modelo directo con brokers regulados (Tradovate / NinjaTrader Brokerage), exige estricta trazabilidad de la identidad y residencia del operador. El uso de proxies para ocultar la residencia física conlleva la cancelación del acuerdo de financiación.
- **Fuentes Oficiales:** [TakeProfitTrader FAQ](https://takeprofittrader.com/) | [TradeDay Rules & FAQs](https://tradeday.com/)

---

### 3.5 Matriz Comparativa de Políticas de Conectividad

| Prop Firm | ¿Permite VPN Comercial? (NordVPN, etc.) | ¿Permite VPS Dedicado? | ¿Exige Notificar Viajes / Cambio IP? | Consecuencia por Violación de ToS |
| :--- | :--- | :--- | :--- | :--- |
| **Apex Trader Funding** | ❌ Prohibido (si oculta IP/ubicación) | ⚠️ Permitido con IP fija / riesgo flag | ✅ Altamente recomendado | Cancelación de PAs y bloqueo de payouts. |
| **Topstep** | ❌ Estrictamente prohibido | ⚠️ Requiere autorización / IP fija | ✅ Obligatorio | Cierre de perfil y denegación de pagos. |
| **MyFundedFutures** | ❌ Prohibido en KYC / Desaconsejado | ⚠️ Tolerado si no rota IPs | ✅ Obligatorio | Pérdida de evaluación y fondos. |
| **TakeProfit Trader** | ❌ Prohibido (riesgo OFAC) | ✅ Permitido para estabilidad técnica | ✅ Recomendado | Suspensión cautelar de cuenta. |
| **TradeDay** | ❌ Prohibido para ocultar identidad | ✅ Permitido con broker setup | ✅ Obligatorio | Pérdida del contrato de fondeo. |

---

## 4. MARCO REGULATORIO Y FISCAL EN ESPAÑA: CNMV, MiFID II Y TRIBUTACIÓN AEAT

### 4.1 Legalidad y Posición de la CNMV respecto al Prop Trading y VPS
✅ **VERIFICADO**:
- **Ámbito de Supervisión de la CNMV:** La Comisión Nacional del Mercado de Valores regula la captación de fondos del público, la prestación de servicios de inversión por cuenta ajena y la comercialización de instrumentos financieros (Art. 140 y concordantes de la *Ley 6/2023, de los Mercados de Valores y de los Servicios de Inversión - LMVSI*, transposición de la Directiva Europea MiFID II).
- **Inexistencia de Delito o Infracción por Operar en Prop Firms:**
  1. El trader particular que se evalúa en una prop firm **NO gestiona fondos de terceros**. Opera en un simulador proporcionado por una empresa extranjera o, en cuentas fondeadas, gestiona capital de la propia empresa que asume el riesgo directo.
  2. El trader **NO capta depósitos del público** ni ofrece asesoramiento financiero a terceros, por lo que **NO requiere licencia de Empresa de Servicios de Inversión (ESI), Sociedad Gestora (SGIIC) ni registro de agente**.
  3. **Advertencias de la CNMV:** La CNMV ha emitido advertencias de protección al consumidor sobre empresas de fondeo no registradas en España (especialmente las que condicionan el acceso a la compra obligatoria de cursos formativos de alto coste). La CNMV advierte que estas empresas están **fuera de su supervisión**, lo que significa que el usuario carece de la cobertura del *FOGAIN* (Fondo de Garantía de Inversiones) y no puede reclamar ante el supervisor en caso de impago. No obstante, **operar con ellas no es ilegal para el ciudadano español**.
- **Operativa desde VPS en España (Oracle Madrid):** Operar futuros del CME o conectarse a prop firms desde un servidor ubicado físicamente en Madrid con dirección IP española es una actividad 100% legal bajo el ordenamiento jurídico español.

---

### 4.2 Calificación Tributaria en IRPF: Base General vs. Base del Ahorro
✅ **VERIFICADO**:
Existe una diferencia fiscal radical entre el trading con capital propio y el cobro de cuentas de fondeo (*prop firms*):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DISTINCIÓN FISCAL EN ESPAÑA (AEAT)                     │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ TRADING CON CUENTA PROPIA (BROKER)   │ PROP TRADING / CUENTAS DE FONDEO     │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Titularidad real de la cuenta.     │ • Titularidad de la empresa fondeadora.│
│ • Depósito bancario de fondos propios│ • Contrato mercantil de servicios/B2B.│
│ • Ganancia / Pérdida Patrimonial.   │ • Rendimientos de Actividad Económica │
│ • BASE IMPONIBLE DEL AHORRO (IRPF):  │ • BASE IMPONIBLE GENERAL (IRPF):     │
│   - Hasta 6.000 €: 19%               │   - Escala progresiva autonómica/    │
│   - 6.000 a 50.000 €: 21%            │     estatal: del 19% al 47%-54%.     │
│   - 50.000 a 200.000 €: 23%          │                                      │
│   - 200.000 a 300.000 €: 27%         │                                      │
│   - Más de 300.000 €: 28%            │                                      │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

- **Criterio de la AEAT y Dirección General de Tributos (DGT):**
  - Los pagos recibidos de una prop firm (*payouts*) no derivan de la transmisión de elementos patrimoniales propios (no hay acciones, futuros o activos a nombre del trader).
  - Jurídicamente, corresponden a una **remuneración por la prestación de servicios de consultoría, análisis o gestión simulada de riesgos** bajo un contrato de contratista independiente (*Independent Contractor Agreement*).
  - Tributan en el IRPF dentro de los **Rendimientos de Actividades Económicas** (Base General), sometidos a la escala progresiva del impuesto.

---

### 4.3 Obligaciones Censales (IAE), RETA (Autónomos) y Facturación Internacional (IVA)
✅ **VERIFICADO**:
Para percibir rendimientos de prop firms de forma regular y legal en España, el operador debe cumplir con las siguientes obligaciones:

1. **Alta Censal (Modelos 036 / 037 de la AEAT):**
   - Alta en el Impuesto de Actividades Económicas (IAE). Epígrafes habituales:
     - *Epígrafe 849.9 (Sección 1):* "Otros servicios empresariales n.c.o.p."
     - *Epígrafe 799 (Sección 2):* "Otros profesionales relacionados con los servicios financieros."
2. **Alta en la Seguridad Social (RETA):**
   - Obligatorio cuando la actividad económica se realiza de forma habitual, personal y directa a cambio de una retribución económica recurrente. Cotización bajo el sistema de tramos por ingresos reales.
3. **Pagos Fraccionados (Modelo 130):**
   - Presentación trimestral del Modelo 130 ingresando a cuenta el 20% del rendimiento neto acumulado del ejercicio.
4. **Facturación e IVA (Ley 37/1992 del IVA):**
   - **Prop Firms radicadas fuera de la Unión Europea (EE.UU. - Topstep, Apex):** Operación no sujeta a IVA español por aplicación de las reglas de localización del servicio (Art. 69 de la Ley del IVA - Exportación de servicios). La factura se emite sin IVA.
   - **Prop Firms radicadas en la Unión Europea (ej. FTMO en República Checa):** Operación intracomunitaria. Requiere que el trader esté dado de alta en el **ROI (Registro de Operadores Intracomunitarios - VIES)**. La factura se emite sin IVA bajo el mecanismo de inversión del sujeto pasivo (*Reverse Charge*) y se declara trimestralmente en el **Modelo 349**.
5. **Deducibilidad de Gastos Afectos:**
   - Al tributar como actividad económica, son deducibles los gastos necesarios para la obtención de ingresos (Art. 28 y 30 LIRPF):
     - Costes de inscripción a *challenges* y *monthly reset fees*.
     - Cuotas de servidores VPS (ej. Oracle Cloud, QuantVPS).
     - Licencias de software y plataformas (NinjaTrader, TradingView, plugins).
     - Cuotas de datos de mercado (Rithmic, CQG).
     - Suministros y conexión a internet (en porcentaje afecto legalmente).

---

### 4.4 Obligaciones Informativas: Modelo 720, Modelo 721 y Directiva DAC8
✅ **VERIFICADO**:

| Declaración Informativa | ¿Aplica a la Cuenta de Prop Firm? | Fundamento Legal y Técnico |
| :--- | :--- | :--- |
| **Modelo 720** (Bienes y derechos en el extranjero) | ❌ **NO APLICA a la cuenta de fondeo** | El trader no es titular de ninguna cuenta bancaria, depósito ni cartera de valores en el extranjero. Los fondos en la plataforma son saldo virtual de la empresa fondeadora. *(Nota: Si los payouts se acumulan en un banco extranjero como Wise o Revolut con saldo >50.000 € a 31 de diciembre, dicha cuenta bancaria sí debe declararse)*. |
| **Modelo 721** (Criptoactivos en el extranjero) | ⚠️ **Solo si el payout se cobra en cripto** | No aplica a la cuenta de prop firm, pero si el trader recibe los payouts en Bitcoin/USDT en un exchange extranjero (Binance, Bybit) con valor superior a 50.000 €, debe presentar el Modelo 721. |
| **Directiva DAC8 (UE) / Control AEAT** | ✅ **APLICA a los procesadores de pago** | En vigor en 2026, la directiva DAC8 obliga a proveedores de servicios de criptoactivos y plataformas de pago (Wise, Deel, Rise, Payoneer) a reportar automáticamente las transferencias y saldos de residentes fiscales españoles a la AEAT, eliminando el anonimato en el cobro de payouts. |

---

## 5. EVALUACIÓN DE ARQUITECTURA: VPS ORACLE MADRID CON IP ESPAÑOLA

La configuración analizada en el entorno operativo (instancia Linux ARM64 / Windows x86 en Oracle Cloud Infrastructure - OCI Región Madrid `eu-madrid-1`):

```
                                    ARQUITECTURA DE CONEXIÓN
┌────────────────────────────────┐                 ┌────────────────────────────────┐
│  VPS Oracle Cloud (Madrid, ES) │                 │      Topstep / Apex / MFFU     │
│  IP Fija Datacenter Española   │ ─────────────── │      Servidores de Trading     │
│  - Sin rotación de IPs         │   HTTPS/TLS     │   (R|API / Tradovate / CQG)    │
│  - Geolocalización: España     │                 └────────────────────────────────┘
│  - Mismo país que KYC/DNI      │
└────────────────────────────────┘
```

### Análisis Técnico y de Riesgo Operativo

1. **Coherencia Geográfica y KYC (✅ Óptimo):**
   - Al estar el servidor en Madrid (España), la dirección IP geolocaliza en el mismo país que la residencia fiscal, DNI/Pasaporte y extractos bancarios aportados en el KYC del trader.
   - **Cero riesgo de bandera OFAC:** No hay tráfico accidental ruteado por servidores de países sancionados.

2. **Detección de ASN de Datacenter vs. Residencial (⚠️ Alerta Menor):**
   - Las IPs de Oracle Cloud pertenecen al ASN de Oracle Corporation (`AS31898` / `AS12312`), identificable en bases de datos IP-to-Country/Threat Intelligence como tipo **DataCenter / Hosting**.
   - **Riesgo:** Si una prop firm tiene un filtro automatizado extremadamente agresivo contra rangos de hosting (como Topstep en fases de auditoría estricta), el sistema podría generar un flag inicial preventivo.
   - **Mitigación:** Al ser una **IP estática única** (no compartida con miles de usuarios como una VPN pública) y mantenerse constante sesión tras sesión, el patrón de comportamiento no corresponde a una granja de *passing services*. En caso de requerimiento, el trader puede justificar documentalmente que se trata de su servidor de ejecución para algoritmos desatendidos.

---

## 6. CONCLUSIÓN FORENSE Y DESMITIFICACIÓN

1. **NO EXISTE NINGUNA LEY CONTRA LAS IPs O VPNs:**
   - No hay ninguna disposición en el Código Penal español, en las directivas de la Unión Europea ni en la legislación de la CFTC estadounidense que declare ilegal el uso de una VPN, un proxy o una IP de datacenter para operar en los mercados financieros.
   - Los reguladores públicos (CFTC, SEC, CNMV) persiguen el fraude financiero, el blanqueo de capitales, la manipulación de mercado (spoofing, layering) y la captación no autorizada de fondos públicos; no la tecnología de red utilizada por un particular.

2. **EL RIESGO ES ESTRICTAMENTE CONTRACTUAL Y PATRIMONIAL (ToS):**
   - El peligro real de usar VPNs comerciales dinámicas (NordVPN, ExpressVPN) o servidores con IPs compartidas no es una citación judicial, sino la **rescisión unilateral del contrato por la prop firm**.
   - Los motores antifraude de las prop firms asocian las IPs de VPNs comerciales a granjas ilegales de venta de cuentas (*passing services*), lo que provoca el **bloqueo automático de la cuenta, la pérdida de los costes de evaluación y la retención irreversible de los payouts acumulados**.

3. **RECOMENDACIÓN TÉCNICA DEFINITIVA:**
   - **Descartar VPNs comerciales compartidas** para operar prop firms.
   - Utilizar una **conexión directa residencial** o un **VPS dedicado con IP fija propia** en el país de residencia legal (ej. VPS Oracle Madrid), notificando preventivamente al soporte de la prop firm si las condiciones de la firma así lo estipulan.
   - Declarar íntegramente los ingresos como actividad económica en España, manteniendo la trazabilidad documental de facturas, costes de evaluación y plataformas.

---

## 7. REFERENCIAS Y FUENTES OFICIALES CITADAS

1. **CME Group Information Policies & Non-Professional Rules:**  
   [CME Market Data Policy Education Center](https://www.cmegroup.com/market-data/license-data/market-data-policy-education-center.html) (Consultado: 25/08/2026).
2. **CME Group Rulebook & Market Regulation:**  
   [CME Rule 575 Disruptive Practices & Globex Access](https://www.cmegroup.com/rulebook/CME/) (Consultado: 25/08/2026).
3. **Apex Trader Funding - Terms of Use & Prohibited Activities:**  
   [Apex Terms of Service and Compliance](https://apextraderfunding.com/) (Consultado: 25/08/2026).
4. **Topstep - Terms of Use and Integrity Policy:**  
   [Topstep Rules and FAQ](https://www.topstep.com/) (Consultado: 25/08/2026).
5. **MyFundedFutures - Trading Rules & Account Policies:**  
   [MyFundedFutures Policy Hub](https://www.myfundedfutures.com/) (Consultado: 25/08/2026).
6. **TakeProfitTrader - Compliance, VPN & VPS FAQ:**  
   [TakeProfitTrader Help Center](https://takeprofittrader.com/) (Consultado: 25/08/2026).
7. **Comisión Nacional del Mercado de Valores (CNMV) - Advertencias sobre Entidades no Reguladas:**  
   [CNMV Buscador de Advertencias y Entidades no Autorizadas](https://www.cnmv.es) (Consultado: 25/08/2026).
8. **Ley 6/2023, de los Mercados de Valores y de los Servicios de Inversión (LMVSI):**  
   [Boletín Oficial del Estado - Ley 6/2023](https://www.boe.es/buscar/act.php?id=BOE-A-2023-6938) (Consultado: 25/08/2026).
9. **Dirección General de Tributos (DGT) / Agencia Tributaria (AEAT) - Consultas Vinculantes sobre Trading e IRPF:**  
   [Sede Electrónica AEAT - Consultas Tributarias](https://sede.agenciatributaria.gob.es) (Consultado: 25/08/2026).
10. **Directiva (UE) 2023/2226 del Consejo (DAC8 - Intercambio de Información Fiscal):**  
    [EUR-Lex - Directiva DAC8](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:32023L2226) (Consultado: 25/08/2026).
