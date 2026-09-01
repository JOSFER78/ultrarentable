# 19 — UI STYLE SPEC: sobrio, gris, simple (2026-09-01)

> Mandato de Emilio: la web debe ser **mucho más intuitiva y simple**, con la estética de la
> aplicación de escritorio de Claude/Cowork: **tonos grises con transparencias, negro y blanco,
> sin colorines**. El único color permitido: **verde para profit/OK y rojo para pérdida/error**.
> Esta spec manda sobre cualquier estilo existente en `apps/web` y se aplica en el carril W5.
> Complementa (no sustituye) a `18_STRATEGIES_PAGE_SPEC.md`: aquella dice QUÉ muestra la página
> de estrategias; esta dice CÓMO se ve todo.

## 1. Principios

1. **Monocromo por defecto.** Todo es escala de grises sobre fondo oscuro. El color es
   información, no decoración: si algo lleva color, es porque es dinero o estado crítico.
2. **Jerarquía por tipografía y espacio, no por color.** Tamaño, peso y separación ordenan la
   página; nada de tarjetas arcoíris, gradientes, ni "badges" de siete colores.
3. **Densidad tranquila.** Pocas cosas por pantalla, bien alineadas, con aire. Una página =
   una pregunta respondida. Lo secundario se pliega o se va a una subpágina.
4. **Honestidad visual (doctrina REAL-ONLY).** `NO EVIDENCE`/`SIN DATOS` se muestra en gris,
   como texto, sin alarma ni relleno. Un 0 real es un 0; una ausencia es una ausencia.
5. **Nada parpadea ni anima** salvo estados de carga discretos.

## 2. Tokens (CSS variables / Tailwind 4 theme)

```css
:root {
  /* Fondos (de atrás hacia delante) */
  --bg:          #0f0f0f;                    /* fondo de página */
  --surface-1:   rgba(255,255,255,0.03);     /* tarjeta / panel */
  --surface-2:   rgba(255,255,255,0.06);     /* hover / panel elevado */
  --surface-3:   rgba(255,255,255,0.10);     /* activo / seleccionado */
  --border:      rgba(255,255,255,0.08);     /* bordes sutiles, 1px siempre */
  --border-strong: rgba(255,255,255,0.16);   /* foco / separadores fuertes */

  /* Texto */
  --text-1:      #ececec;   /* principal */
  --text-2:      #a6a6a6;   /* secundario, labels */
  --text-3:      #6f6f6f;   /* terciario, hints, NO EVIDENCE */

  /* Los ÚNICOS colores */
  --profit:      #34d399;   /* verde: PnL positivo, PASSED, certificada, activo OK */
  --loss:        #f87171;   /* rojo: PnL negativo, FAILED, error, cuenta reventada */
  /* variantes tenues para fondos de celda */
  --profit-dim:  rgba(52,211,153,0.12);
  --loss-dim:    rgba(248,113,113,0.12);
}
```

- **Prohibido** introducir otros colores (azules, ámbar, morados). Un warning se expresa en
  gris con icono/texto ("⚠ datos 08-2026 sin re-verificar"), no en amarillo.
- Tipografía: una sola familia sans del sistema (`ui-sans-serif/Inter`); monoespaciada solo
  para hashes, ids y números tabulares (`font-variant-numeric: tabular-nums` en tablas).
- Radios 8px, sombras casi nulas (la elevación la dan las transparencias), transiciones ≤150ms.

## 3. Reglas por componente

| Componente | Regla |
| :--- | :--- |
| **Sidebar** | Estrecho, gris, las 8 entradas de la misión (Inicio · Estrategias · Candidatos · Gates · Fondeo · Prop-firms · Plan · Sistema) **+ al final, atenuada: "Ultra — EN CONSTRUCCIÓN"** (visible siempre, texto `--text-3`). Activo = `--surface-3` + texto `--text-1`; nada de iconos de colores |
| **Header** | Título de página + versión REAL del motor (dinámica) + estado de conexión API en gris (verde solo si se quiere marcar "operativo", punto de 6px) |
| **Tablas** | El corazón de la app. Cabecera `--text-2` uppercase 11px; filas separadas por `--border`; números alineados a la derecha, tabulares; PnL/PF en `--profit`/`--loss` según signo; el resto SIEMPRE gris. Orden y filtro nativos, sin librerías pesadas |
| **Estados de estrategia** | Texto plano con prefijo: `CERTIFIED_CURRENT` (verde), `REJECTED_*`/`BUSTED` (rojo), todo lo demás (`EXTRACTED`, `BACKTEST_VERIFIED`, `LEGACY_*`, `EN MEJORA`…) gris `--text-2`. Nunca chips multicolor |
| **Métricas sin evidencia** | `NO EVIDENCE` en `--text-3`, cursiva opcional. Jamás 0, jamás guion ambiguo |
| **Botones** | Primario: fondo `--surface-3`, borde `--border-strong`, texto `--text-1`. Peligro: borde `--loss`. Sin botones verdes/azules de marketing |
| **Gráficas (equity, embudos)** | Línea gris clara sobre fondo transparente; área bajo curva `--surface-2`; drawdown en `--loss-dim`; sin rejillas densas ni leyendas de colores |
| **Banners** | `EN CONSTRUCCIÓN` (rutas ULTRA): franja gris con texto `--text-2`. Errores de API: franja con borde `--loss` y el error literal |
| **Formularios/filtros** | Inputs `--surface-1` con borde `--border`; foco = `--border-strong`. Selects nativos estilizados, sin dropdowns exóticos |

## 4. Estructura de páginas (simplicidad)

- **Páginas maestras con subpáginas jerarquizadas** (decisión sellada #16), siguiendo la
  arquitectura modular M1-M4 (`orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md`):
  `/estrategias` es la maestra con sus secciones (Generación · Mejora · Valoración · Meta), no
  ocho páginas sueltas compitiendo.
- Cada página abre con **una línea de estado honesta** (ej: "Certificadas: 0 · Motor 5.17.0 ·
  Última campaña: hoy 10:11") antes que cualquier tabla.
- Nada de dashboards de vanidad: si un número no ayuda a decidir, no está.

## 5. Verificación (entra en el checklist de W5)

1. `grep` de clases/estilos: cero colores fuera de los tokens (`#`hex ajenos, `blue`, `amber`,
   `purple`… no aparecen).
2. Captura de cada página en build de producción: solo grises + verde/rojo semántico.
3. Contraste AA mínimo: `--text-1` sobre `--bg` ≥ 12:1; `--text-3` reservado a texto no esencial.
4. Los 5 puntos con `v5.4.0` hardcodeado sustituidos por la versión dinámica.
