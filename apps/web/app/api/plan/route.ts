import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";
import { findRepoRoot } from "@/lib/projectPaths";

export const dynamic = "force-dynamic";

import { obtenerFasesPlanData, type FaseCalculada } from "@/lib/fasesServer";
import type { TareaTablero } from "@/lib/tableroServer";

export interface PlanBloque {
  id: string;
  titulo: string;
  estado: string;
  estado_calculado?: string;
  depende_de: string[];
  desbloquea: string[];
  verificacion_global: string;
  actualizado: string;
  aparcado: boolean;
  motivo_aparcado: string;
  archivo: string;
  content: string;
  tareas_totales: number;
  tareas_completadas: number;
  avance?: string;
  tareas?: TareaTablero[];
  es_activa?: boolean;
}

interface PlanBloqueError {
  archivo: string;
  error: string;
}

export interface DoctrinaRegla {
  id: string;
  numero: number;
  titulo: string;
  descripcion: string;
  icono: string;
  categoria: "real_only" | "criterio_1_1" | "motor_version" | "gobernanza";
}

export interface ModuloPipeline {
  id: "M1" | "M2" | "M3" | "M4" | "M5";
  nombre: string;
  subtitulo: string;
  mision: string;
  motor_o_herramienta: string;
  estado: "ACTIVO_VPS" | "EN_CURSO" | "LISTO_CONTRATO" | "BLOQUEADO_POR_DATOS" | "IMPLEMENTADO";
  estado_label: string;
  metricas_clave: string[];
  salida_contrato: string;
}

export interface WebRutaEspec {
  ruta: string;
  nombre: string;
  modulo: string;
  proposito: string;
  estado: "IMPLEMENTADA" | "PARCIAL" | "EN_REVISION" | "APARCADA";
  fuente_datos: string;
  muestra: string[];
  nunca_muestra: string[];
}

export interface HudStatus {
  motor_version: string;
  certificadas_fondeo: number;
  meta_estrategias: number;
  campana_activa: string;
  campana_estado: string;
  criterio_sellado: string;
  vps_status: string;
  api_status: string;
  alertas_activas: string[];
  ultimo_hallazgo: string;
}

export interface PlanApiResponse {
  generatedAt: string;
  source: string;
  count: number;
  fase_activa: string;
  fases: FaseCalculada[];
  bloques: PlanBloque[];
  errores: PlanBloqueError[];
  hud: HudStatus;
  doctrina: DoctrinaRegla[];
  pipeline: ModuloPipeline[];
  rutas_web: WebRutaEspec[];
}

const FRONTMATTER_RE = /^---\r?\n([\s\S]*?)\r?\n---/;
const BLOQUE_FILENAME_RE = /^F\d{2}_.*\.md$/;
const FIELD_LINE_RE = /^([a-zA-Z_][\w]*):\s*(.*)$/;
const QUOTED_ITEM_RE = /"([^"]*)"/g;

function parseFrontmatterValue(raw: string): string | string[] {
  const trimmed = raw.trim();
  if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
    const items: string[] = [];
    let match: RegExpExecArray | null;
    QUOTED_ITEM_RE.lastIndex = 0;
    while ((match = QUOTED_ITEM_RE.exec(trimmed)) !== null) {
      items.push(match[1]);
    }
    return items;
  }
  if (trimmed.startsWith('"') && trimmed.endsWith('"') && trimmed.length >= 2) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function parseBloqueFile(filePath: string, filename: string): PlanBloque | PlanBloqueError {
  let raw: string;
  try {
    raw = fs.readFileSync(filePath, "utf-8");
  } catch (error) {
    return { archivo: filename, error: `No se pudo leer el fichero: ${String(error)}` };
  }

  const match = raw.match(FRONTMATTER_RE);
  if (!match) {
    return { archivo: filename, error: "El fichero no empieza con frontmatter YAML (---...---)" };
  }

  const fields: Record<string, string | string[]> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const lineMatch = line.match(FIELD_LINE_RE);
    if (!lineMatch) continue;
    fields[lineMatch[1]] = parseFrontmatterValue(lineMatch[2]);
  }

  const scalar = (key: string): string | null => {
    const value = fields[key];
    return typeof value === "string" && value.length > 0 ? value : null;
  };
  const array = (key: string): string[] => {
    const value = fields[key];
    return Array.isArray(value) ? value : [];
  };

  const id = scalar("id");
  const titulo = scalar("titulo");
  const estado = scalar("estado");
  if (!id || !titulo || !estado) {
    return {
      archivo: filename,
      error: `Frontmatter incompleto (faltan id/titulo/estado)`,
    };
  }

  const bodyContent = raw.slice(match[0].length).trim();

  // Contar tareas en tablas (| W... o | B... o | E...)
  const taskRows = bodyContent.split("\n").filter((l) => /^\|\s*(W|B|E|A|S)\d+/i.test(l.trim()));
  const completedRows = taskRows.filter((l) => /✅|HECHO|DONE/i.test(l));

  return {
    id,
    titulo,
    estado,
    depende_de: array("depende_de"),
    desbloquea: array("desbloquea"),
    verificacion_global: scalar("verificacion_global") ?? "",
    actualizado: scalar("actualizado") ?? "",
    aparcado: (scalar("aparcado") ?? "").toLowerCase() === "true",
    motivo_aparcado: scalar("motivo_aparcado") ?? "",
    archivo: filename,
    content: bodyContent,
    tareas_totales: taskRows.length > 0 ? taskRows.length : 1,
    tareas_completadas: completedRows.length,
  };
}

const DOCTRINA_ITEMS: DoctrinaRegla[] = [
  {
    id: "REAL_ONLY",
    numero: 1,
    titulo: "Doctrina REAL-ONLY & Cero Mocks",
    descripcion: "Prohibición absoluta de datos sintéticos o inventados. Sin evidencia física en disco o BD canónica se muestra SIN EVIDENCIA / NO DATA. Cero generación aleatoria en validaciones.",
    icono: "ShieldCheck",
    categoria: "real_only",
  },
  {
    id: "CRITERIO_1_1",
    numero: 2,
    titulo: "Criterio 1.1 Institucional Sellado",
    descripcion: "Filtro innegociable de certificación: ≥ 200 trades fuera de muestra (OOS), Factor de Beneficio OOS ≥ 1.25, ratio OOS/IS ≥ 0.5, DSR positivo y las 11 comprobaciones con evidencia física individual.",
    icono: "Award",
    categoria: "criterio_1_1",
  },
  {
    id: "REGLA_26",
    numero: 3,
    titulo: "Regla #26: Versionado Estricto de Motor",
    descripcion: "Cualquier ajuste que altere las operaciones producidas sube CURRENT_ENGINE_VERSION. Las certificaciones anteriores pasan a LEGACY y dejan de contar como válidas. Nunca se maquilla ni se borra un histórico.",
    icono: "Cpu",
    categoria: "motor_version",
  },
  {
    id: "PERSISTENCIA_DISCO",
    numero: 4,
    titulo: "Persistencia Inmediata en Disco",
    descripcion: "Nada valioso vive solo en memoria RAM. Toda población, candidato o telemetría se persiste a disco con hash SHA-256 de forma atómica para resistir reinicios del sistema.",
    icono: "HardDrive",
    categoria: "real_only",
  },
  {
    id: "NUNCA_RM",
    numero: 5,
    titulo: "Nunca 'rm' — Cuarentena Sellada",
    descripcion: "Queda terminantemente prohibido borrar código o archivos obsoletos con rm. Todo componente retirado se traslada a cuarentena/ con manifiesto criptográfico SHA-256 y causa documentada.",
    icono: "Archive",
    categoria: "gobernanza",
  },
  {
    id: "GOBERNANZA_RECURSOS",
    numero: 6,
    titulo: "Gobernanza de Recursos (VPS & PC)",
    descripcion: "Un solo proceso pesado simultáneo bajo nice -n 19 y cgroups en Linux. Protección estricta contra saturación de CPU y swap. Control del carril de minería desacoplado.",
    icono: "Gauge",
    categoria: "gobernanza",
  },
];

const PIPELINE_MODULOS: ModuloPipeline[] = [
  {
    id: "M1",
    nombre: "Generación Masiva",
    subtitulo: "StrategyQuant X (SQX) al 100%",
    mision: "Exprimir StrategyQuant X en VPS headless (sqcli :5050) sobre datasets de futuros CME regulados (ES/NQ 5m/15m). Producir el máximo caudal de estrategias crudas viables (.sqx + CSV de métricas).",
    motor_o_herramienta: "StrategyQuant X Pro Build 144 (:5050) + Datasets CME",
    estado: "ACTIVO_VPS",
    estado_label: "Headless en VPS (:5050)",
    metricas_clave: [
      "Instalación real: ~/StrategyQuantX144",
      "Símbolos activos: ES_M5, ES_M15, NQ_M5, NQ_M15",
      "Ingesta continua de crudas a ToImprove/",
      "Registro de linaje y config-hash por lote",
    ],
    salida_contrato: "Archivos .sqx crudos con AST parseado, config_hash y procedencia persistida",
  },
  {
    id: "M2",
    nombre: "Bucle de Mejora",
    subtitulo: "Loop Iterativo & Telemetría",
    mision: "Tomar crudas de M1 o near-misses y someterlas a un ciclo cerrado con revisión del motor en cada vuelta. Blind holdout intocado; penalización de multiplicidad (DSR). Las fallidas se etiquetan honestamente para alimentar el refinamiento.",
    motor_o_herramienta: "Motor de Validación 5.18.0 + Embudo de Telemetría",
    estado: "EN_CURSO",
    estado_label: "Campaña E2 15m en curso",
    metricas_clave: [
      "Telemetría de embudos (orchestration/results/telemetria/)",
      "Descarte honesto en IS (400 sin ventaja bruta, 20 coste en 5m)",
      "Presupuesto de iteraciones acotado por DSR",
      "Holdout ciego garantizado sin fuga de datos",
    ],
    salida_contrato: "Candidatas con historial completo de iteraciones y uplift mediano de PF OOS",
  },
  {
    id: "M3",
    nombre: "Valoración & Fondeo",
    subtitulo: "11 Gates & Exámenes Prop Firms",
    mision: "Someter a las candidatas que superan M2 a las reglas barra a barra de las cuentas de fondeo reales (Topstep, MFFU, TradeDay). Monte Carlo sobre equity flotante para medir P(pasar en ≤8 días) y P(romper cuenta ≤20%).",
    motor_o_herramienta: "Simulador de Reglas Prop (Motor 5.15.0+) + Monte Carlo",
    estado: "LISTO_CONTRATO",
    estado_label: "Simulador Barra a Barra Listo",
    metricas_clave: [
      "11 Gates de auditoría física individual",
      "P(pasar ≤8 días) calculada con equity flotante",
      "P(ruina 6 meses) ≤ 20% como techo innegociable",
      "Objetivo: ≥20% mensual sostenible mediana",
    ],
    salida_contrato: "Ranking de idoneidad: Estrategia × Firma de fondeo con sizing exacto en microcontratos",
  },
  {
    id: "M4",
    nombre: "Candidatos Estrategias",
    subtitulo: "578 Candidatas Individuales",
    mision: "Exploración tabular y archivo técnico de las candidatas individuales evaluadas en SQLite (Fondeo CME y Ultra Cripto). Trazabilidad de linaje, scorecards y filtros institucionales por activo y temporalidad.",
    motor_o_herramienta: "SQLite DB + Candidates API (/api/v1/candidates)",
    estado: "IMPLEMENTADO",
    estado_label: "578 Candidatas SQLite",
    metricas_clave: [
      "578 candidatas canónicas con procedencia sellada",
      "Filtros por Profit Factor, Drawdown y Trades OOS",
      "Exportación CSV / XLSX con hashes criptográficos",
      "Pestañas de ruta: Fondeo CME vs Ultra Cripto",
    ],
    salida_contrato: "Dataset normalizado de candidatas disponible para backtest y asignación",
  },
  {
    id: "M5",
    nombre: "Candidatos Meta-Estrategias",
    subtitulo: "Composición Descorrelacionada",
    mision: "Combinar múltiples estrategias certificadas de M3 en una cartera compuesta para reducir la varianza conjunta y aniquilar el drawdown. Router dinámico con límites deterministas (Meta-Fondeo y Meta-Ultra).",
    motor_o_herramienta: "Router de Meta-Estrategias (services/meta/)",
    estado: "BLOQUEADO_POR_DATOS",
    estado_label: "Espera ≥2 Certificadas Fondeo",
    metricas_clave: [
      "Correlación por solape temporal de trades reales",
      "Optimización ERC / Min-Varianza para fondeo",
      "Atenuación de colas izquierdas de drawdown",
      "Protección contra quiebra simultánea de cuentas",
    ],
    salida_contrato: "Meta-estrategia ensamblada con pesos de asignación y circuit breakers globales",
  },
];

const RUTAS_WEB_CATALOGO: WebRutaEspec[] = [
  {
    ruta: "/",
    nombre: "Portada Maestro",
    modulo: "Global",
    proposito: "Responder en 5 segundos: ¿Hay algo listo para operar? ¿Cuál es el estado del motor y la última campaña?",
    estado: "IMPLEMENTADA",
    fuente_datos: "/api/v1/discovery/status, /api/v1/candidates, telemetría de embudos",
    muestra: ["Versión de motor vigente", "Estrategias listas para fondeo", "Métricas de última campaña E2", "Enlaces solo a páginas vivas"],
    nunca_muestra: ["Tarjetas grandilocuentes sin datos", "Cifras calculadas a mano", "Aprobaciones antiguas como si fueran válidas"],
  },
  {
    ruta: "/estrategias",
    nombre: "Maestra de Estrategias",
    modulo: "M1–M4",
    proposito: "Lista exclusiva de estrategias certificadas vigentes con todo lo necesario para pasarlas a examen o trading.",
    estado: "IMPLEMENTADA",
    fuente_datos: "/api/v1/certified, /api/v1/discovery/status",
    muestra: ["Tabla de estrategias válidas", "11 Gates con evidencia", "Módulos M1-M4 con estado en una línea", "Explicación si hay 0 vigentes"],
    nunca_muestra: ["Estrategias fallidas mezcladas", "Gates deducidos de estados booleanos", "Paneles técnicos no funcionales"],
  },
  {
    ruta: "/prop-firms",
    nombre: "Catálogo Maestro Prop Firms",
    modulo: "Fondeo CME",
    proposito: "Las reglas exactas y auditadas de las firmas de fondeo de futuros CME con las que se examinan las estrategias.",
    estado: "IMPLEMENTADA",
    fuente_datos: "Tabla verificada de 6 firmas CME con enlaces SourceRef a términos oficiales",
    muestra: ["Topstep, Apex, MFFU, TradeDay, Take Profit Trader, Tradeify", "11 columnas de métricas oficiales", "Fichas de auditoría SourceRef"],
    nunca_muestra: ["Reglas asumidas sin enlace oficial", "Cupones no verificados", "Afiliaciones no autorizadas"],
  },
  {
    ruta: "/tradesfera",
    nombre: "Tratado Maestro Tradesfera",
    modulo: "Doctrina & Educación",
    proposito: "Texto y herramientas prácticas basadas en los 16 manuales técnicos de Tradesfera (Vicente Pons / Gerard García).",
    estado: "IMPLEMENTADA",
    fuente_datos: "docs/tradesfera/ (Módulos M01 a M16)",
    muestra: ["Calculadora binomial M02", "Simulador EOD vs Intraday M03", "Dimensionador de micros M04", "Reloj Killzones NY M11", "Playbook M16"],
    nunca_muestra: ["Formulaciones mágicas", "Cifras sin soporte en el tratado", "Simulaciones desconectadas del texto"],
  },
  {
    ruta: "/plan",
    nombre: "Plan Maestro & Orquestación",
    modulo: "Gobernanza",
    proposito: "Centro de control visual del proyecto: Roadmap F00-F09, Pipeline M1-M4 con StrategyQuant X, Doctrina y Especificación Web.",
    estado: "IMPLEMENTADA",
    fuente_datos: "orchestration/state/ (bloques Fxx, current_phase, plan_maestro, especificación)",
    muestra: ["HUD visual de telemetría", "Roadmap de Fases F00-F09 con barras de tareas", "Pipeline visual M1-M4", "Doctrina del sistema en 4 cuadrantes"],
    nunca_muestra: ["Volcados masivos de texto crudo en la cabecera", "Fases inventadas", "Planes desincronizados del disco"],
  },
  {
    ruta: "/trading-desk",
    nombre: "Trading Desk (Mesa de Operación)",
    modulo: "Operación",
    proposito: "Supervisar y ejecutar las estrategias certificadas en cuentas de fondeo reales.",
    estado: "PARCIAL",
    fuente_datos: "API de cuentas y posiciones (sin motor conectado en vivo)",
    muestra: ["Estructura de mesa de trading", "Aviso honesto de 'Sin motor conectado'"],
    nunca_muestra: ["Saldos o balances simulados", "Curvas de equidad forjadas", "Operaciones falsas"],
  },
  {
    ruta: "/sistema",
    nombre: "Diagnóstico del Sistema",
    modulo: "Infraestructura",
    proposito: "Monitorización del estado de salud de la API, el motor, los servicios del VPS y los datasets.",
    estado: "PARCIAL",
    fuente_datos: "/api/local/status, /api/v1/discovery/status",
    muestra: ["Estado de servicios locales y remotos", "Versión de dependencias", "Últimos eventos del sistema"],
    nunca_muestra: ["Estados de 'OK' engañosos cuando un servicio está caído"],
  },
];

export async function GET() {
  const repoRoot = findRepoRoot();
  const stateDir = path.join(repoRoot, "orchestration", "state");
  const bloquesDir = path.join(stateDir, "plan", "bloques");

  const bloques: PlanBloque[] = [];
  const errores: PlanBloqueError[] = [];

  if (fs.existsSync(bloquesDir)) {
    const filenames = fs
      .readdirSync(bloquesDir)
      .filter((name) => BLOQUE_FILENAME_RE.test(name))
      .sort();

    for (const filename of filenames) {
      const result = parseBloqueFile(path.join(bloquesDir, filename), filename);
      if ("error" in result) errores.push(result);
      else bloques.push(result);
    }
    bloques.sort((a, b) => a.id.localeCompare(b.id));
  }

  const fasesPlan = obtenerFasesPlanData();
  const fasesMap = new Map(fasesPlan.fases.map((f) => [f.id, f]));

  for (const b of bloques) {
    const calc = fasesMap.get(b.id);
    if (calc) {
      b.tareas = calc.tareas;
      b.avance = calc.avance_label;
      b.estado_calculado = calc.estado_calculado;
      b.es_activa = calc.es_activa;
      b.tareas_totales = calc.total_tareas;
      b.tareas_completadas = calc.verificadas;
    } else {
      b.tareas = [];
      b.avance = "0 de 0";
      b.estado_calculado = "esperando turno";
      b.es_activa = false;
    }
  }

  const hud: HudStatus = {
    motor_version: "5.18.0",
    certificadas_fondeo: 0,
    meta_estrategias: 0,
    campana_activa: "E2 (ES 5m/15m) B03/B04",
    campana_estado: "5m terminada (420/420 muertas IS); 15m en curso desacoplada en VPS",
    criterio_sellado: "Criterio 1.1 Institucional (≥200 trades OOS, PF ≥1.25, 11 gates)",
    vps_status: "OPERATIVO (Oracle Cloud 4 núcleos / 23 GB RAM, sqcli en :5050)",
    api_status: "ACTIVA (FastAPI :8000 / Web :3100 producción)",
    alertas_activas: [
      "Campaña E2 15m corriendo bajo gobernanza en VPS",
      "Hallazgo auditado: Comisión MES corregida a 0.60 USD (Issue #38 para Motor 5.19.0)",
      "Licencia StrategyQuant X caduca 05-09-2026 (acción requerida)",
    ],
    ultimo_hallazgo: "E2 5m: 400 configs sin ventaja bruta, 20 consumidas por fricción en SESSION_MOMENTUM; ninguna murió por falta de operaciones.",
  };

  return NextResponse.json({
    generatedAt: new Date().toISOString(),
    source: bloquesDir,
    count: bloques.length,
    fase_activa: fasesPlan.fase_activa,
    fases: fasesPlan.fases,
    bloques,
    errores,
    hud,
    doctrina: DOCTRINA_ITEMS,
    pipeline: PIPELINE_MODULOS,
    rutas_web: RUTAS_WEB_CATALOGO,
  });
}
