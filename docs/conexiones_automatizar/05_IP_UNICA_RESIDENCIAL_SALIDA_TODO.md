---
tipo: guia-operativa
proyecto: 01 Ultrarentable
categoria: conexiones-automatizar
fecha: 2026-08-25
ficha_maestra: "[[Ultrarentable]]"
estado: historico — transición de decisión; la solución DEFINITIVA es [[09_PROXY_ISP_RESIDENCIAL_SOLUCION_UNICA]]
verificacion_entorno_real: 2026-08-25
tags: [ultrarentable, ip-unica, tailscale-exit-node, prop-firms, arm64, hermes]
---

# 🎯 IP ÚNICA RESIDENCIAL para TODO el sistema (VPS ARM64 + Hermes) — Guía verificada

> [!NOTE]
> **Documento histórico de transición.** Registra cómo evolucionó la decisión de la IP única (exit-node PC → Oracle directa → **Proxy ISP estático**, la definitiva en `09`). El §4b refleja el análisis que llevó a descartar el exit-node. Leer `09` como fuente canónica.

> **Requisito del usuario:** todo el tráfico de trading (Tradovate, NinjaTrader, TradingView, prop firms) debe salir por UNA MISMA IP, sin infringir reglas de las firms. El VPS Linux está 24/7 y ahí vive Hermes → prioridad solución nativa Linux.
>
> **Estado real verificado HOY en el VPS (2026-08-25):**
> - IP pública actual: `143.47.35.167` — **AS31898 Oracle Corporation, datacenter (Madrid)** ❌ no sirve como identidad ante firms estrictas.
> - Tailscale activo en el VPS (`100.104.148.117`) con peer `pc` (Windows) **online, conexión directa en 14ms**.
> - La IP residencial de tu casa es **`79.117.189.155`** — DIGI Spain Telecom (AS57269), hostname `digimobil.es`, **IP española residencial real** ✅.
> - ⚠️ El PC todavía NO está configurado como exit node (`tailscale exit-node list` → "no exit nodes found"). Es el único paso que falta.

---

## 1. Por qué esta es LA solución a tu requisito "una sola IP"

| Requisito firm | Cómo lo resuelve |
|---|---|
| Misma IP para login + trading | Todo sale por `79.117.189.155` (tu casa): VPS, Hermes, bots, navegadores — una sola identidad |
| No VPN comercial detectable | Tailscale/WireGuard punto a punto NO aparece como VPN comercial; la salida es fibra residencial DIGI con ASN doméstico |
| Consistencia de IP (MFFU etc.) | Tu IP residencial es estable; mucho más que un datacenter con IP flotante |
| Topstep (prohíbe VPS/datacenter) | La plataforma NT8/TopstepX ve la IP residencial de casa |

**Cuidado importante:** si la firma exige "operar desde tu dispositivo local", lo que ven es la IP — y será tu casa. Pero si algún día te preguntan, sé transparente con la arquitectura; varias firms (MFFU, FundedNext) permiten explícitamente VPS con IP consistente.

## 2. Arquitectura objetivo

```
┌──────────── TU CASA ────────────┐         ┌──── VPS Oracle ARM64 (24/7) ────┐
│  PC Windows (exit node Tailscale)│ ◄─14ms─►│  Motor Python + Hermes + crons  │
│  Salida internet:                │ Tailscale│        │                        │
│  79.117.189.155 (DIGI resid.)    │  direct  │  Todo el tráfico TRADING sale   │
└──────────────────────────────────┘          │  vía exit-node → TU IP de casa  │
                                              └────────────────────────────────┘
```

- **Solo el tráfico de trading** se enruta por el exit node (con namespace de red o policy routing), para que SSH/actualizaciones del VPS no dependan de que tu PC esté encendido.
- Riesgo operativo asumible: si el PC de casa se apaga, los bots pierden salida → kill-switch FAIL-CLOSED detiene órdenes (nunca opera desde la IP de Oracle).

## 3. Pasos exactos (en orden)

### Paso A — En el PC Windows (2 minutos)
1. Tailscale icono → **Preferences → "Run as exit node"** (o admin PowerShell):
   ```powershell
   tailscale up --advertise-exit-node
   ```
2. Windows crea automáticamente el NAT compartido al activarlo desde la GUI; si usas solo CLI:
   ```powershell
   # Reenvío IP + NAT (PowerShell admin)
   Set-NetIPInterface -Forwarding Enabled -InterfaceAlias "Wi-Fi"   # o "Ethernet"
   Set-NetIPInterface -Forwarding Enabled -InterfaceAlias "Tailscale"
   ```
3. En el admin de Tailscale (https://login.tailscale.com/admin/machines): máquina `pc` → ⋯ → **Edit route settings** → aprobar el exit node (subred anunciada).

### Paso B — En el VPS (ya tienes Tailscale instalado)
1. Autorizar el uso:
   ```bash
   sudo tailscale up --accept-routes --advertise-exit-node=false
   ```
2. **Proteger SSH antes de nada** (evita lockout si enrutas TODO):
   ```bash
   # Opción segura recomendada: NO cambiar la ruta por defecto del VPS entero;
   # enrutar SOLO los procesos de trading con netns (paso B3).
   ```
3. **Aislamiento por network namespace (recomendado — prioridad Linux):**
   ```bash
   sudo ip netns add trading
   sudo ip link add v-trading type veth
   sudo ip link set v-trading netns trading
   # ... bridge con br0 hacia tailscale0 con ruta default via exit node ...
   # Los bots/Hermes-crons corren así:
   sudo ip netns exec trading systemctl start ultrarentable-bot
   ```
   Receta completa de netns+veth+policy routing: doc `01_VPN_IP_SEGURO_VPS_FONDEO.md` §"Network Namespaces".
4. Verificación REAL (obligatoria antes de operar):
   ```bash
   sudo ip netns exec trading curl -s https://ifconfig.me   # debe devolver 79.117.189.155
   sudo ip netns exec trading curl -s https://ipinfo.io     # org: DIGI Spain (no Oracle)
   ```

### Paso C — Kill-switch FAIL-CLOSED (obligatorio)
Si el túnel cae y el tráfico vuelve a salir por Oracle → cancelar órdenes y parar bots. Script Python completo en `01_VPN_IP_SEGURO_VPS_FONDEO.md` §"Network Guard". Resumen:
```python
# cada 10s: if public_ip != '79.117.189.155': cancel_all_orders(); stop_bots()
```
Y añádelo como cronjob Hermes de supervisión (junto a risk_watchdog del doc 04).

## 4b. ⭐ MODO 100% LINUX EN EL VPS (decisión del usuario 2026-08-25): TODO corre en el VPS donde vive Hermes

El usuario quiere controlar TODO desde Hermes en el VPS ARM64, sin depender del PC de casa encendido. Tres configuraciones posibles, todas gestionables 100% desde el propio VPS:

### Opción A — Sin túnel: salir por la IP estática de Oracle (`143.47.35.167`)
- **Coste:** $0 · **Misma IP siempre:** ✅ (IP estática del VPS) · **Control total vía Hermes:** ✅
- **Requisito:** elegir SOLO firms que toleran VPS/datacenter con IP fija.
- Según investigación del 2026-08-25: FundedNext permite VPS exigiendo IP dedicada fija; MFFU exige consistencia de IP; **Topstep prohíbe datacenter** (descártala en este modo).
- ⚠️ HIPÓTESIS a confirmar con cada firma antes de abrir cuenta: que su filtro acepta explícitamente un ASN de hosting con IP estable. Algunas firms solo banean si detectan la IP *cambiando*, no por ser datacenter.
- Ventaja estructural: cero piezas móviles, latencia mínima a CME, nada que se rompa.

### Opción B — Proxy residencial estático ISP en el VPS (tun2socks)
- **Coste:** ~$5–15/mes · **Misma IP siempre:** ✅ · **Todo en el VPS:** ✅
- El tráfico de trading sale por una IP residencial fija contratada; SSH/sistema siguen por Oracle.
- Configuración tun2socks + systemd ya documentada en `01_VPN_IP_SEGURO_VPS_FONDEO.md` §Solución 3.
- Compatible también con firms estrictas tipo Topstep (la salida es residencial).

### Opción C — NordVPN Dedicated IP en el VPS
- **Coste:** suscripción NordVPN + suplemento (~$5–10/mes extra) · **Misma IP:** ✅
- Cliente oficial existe para ARM64. Contra: el rango pertenece a NordVPN y algunas firms filtran rangos VPN conocidos. Opción más débil para fondeo.

**Recomendación coherente con tu prioridad Linux:** empezar por **Opción A** ($0, todo nativo en el VPS) eligiendo una firma que tolere datacenter-IP-fija, y tener la **Opción B** como plan B si la firma elegida resulta filtrar hosting. La solución exit-node-vía-PC queda descartada como principal (depende del PC encendido); solo útil como respaldo puntual.

En TODAS las opciones el kill-switch y los crons de vigilancia de IP corren en el propio VPS bajo Hermes — control único desde este chat.

## 5. Qué queda pendiente de decidir/ejecutar (actualizado a decisión "todo en el VPS")

1. ⏳ Elegir firma objetivo que tolere IP datacenter fija (candidatas: FundedNext, MFFU — confirmar con soporte ANTES de pagar evaluación).
2. ⏳ Decirle al soporte de la firma, si aplica, la IP estática `143.47.35.167` para whitelist.
3. ⏳ Implementar kill-switch + cronjob Hermes de vigilancia de IP (alerta si la IP pública cambia).
4. Plan B si la firma filtra hosting: contratar proxy ISP residencial estático y montar tun2socks (§Opción B).
5. La ruta exit-node-vía-PC queda como respaldo manual puntual, no como arquitectura principal.
