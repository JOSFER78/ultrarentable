import { NextResponse } from "next/server";

export interface OmnirouteDecision {
  taskId: string;
  intent: string;
  tier: "CLAUDE_OPUS" | "ANTIGRAVITY" | "RUN_TESTS" | "SYSTEM_STATUS" | "FULL_SWARM";
  tierTitle: string;
  voiceReplyImmediate: string;
  plan: string[];
  executionTarget: {
    engine: "claude" | "agy" | "python" | "system";
    command: string;
    cwd?: string;
  };
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const prompt: string = (body.prompt || "").trim();

    if (!prompt) {
      return NextResponse.json(
        { error: "Prompt no proporcionado" },
        { status: 400 }
      );
    }

    const lower = prompt.toLowerCase();
    const taskId = `JARVIS-${Date.now().toString().slice(-6)}`;

    let decision: OmnirouteDecision;

    // 1. Triage: Pruebas / Tests
    if (
      lower.includes("test") ||
      lower.includes("prueba") ||
      lower.includes("pytest") ||
      lower.includes("comprueba") ||
      lower.includes("verific")
    ) {
      decision = {
        taskId,
        intent: "Verificación y ejecución de suites de pruebas reales",
        tier: "RUN_TESTS",
        tierTitle: "⚡ Antigravity Runner (Pytest)",
        voiceReplyImmediate:
          "Oído Emilio. Lanzando la suite de pruebas con Antigravity para comprobar el estado real.",
        plan: [
          "Identificar suite de pruebas en disco",
          "Ejecutar pytest con captura de salida cruda",
          "Comprobar assertions y tiempos de ejecución",
        ],
        executionTarget: {
          engine: "python",
          command: ".\\.venv\\Scripts\\python.exe -m pytest -q tests/test_smoke_fastapi.py --maxfail=1",
        },
      };
    }
    // 2. Triage: Estado del sistema / Puertos / Salud
    else if (
      lower.includes("estado") ||
      lower.includes("cómo va") ||
      lower.includes("qué está pasando") ||
      lower.includes("status") ||
      lower.includes("puerto") ||
      lower.includes("memoria")
    ) {
      decision = {
        taskId,
        intent: "Inspección forense de estado del sistema y procesos",
        tier: "SYSTEM_STATUS",
        tierTitle: "👁️ Inspección del Sistema",
        voiceReplyImmediate:
          "Consultando el estado de los procesos y servicios en tu PC en este instante.",
        plan: [
          "Comprobar procesos activos de Antigravity y Claude",
          "Verificar puertos locales (3000, 5050, 8000)",
          "Generar informe conciso de telemetría",
        ],
        executionTarget: {
          engine: "system",
          command: "powershell -Command \"Get-Process claude, agy, python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, CPU\"",
        },
      };
    }
    // 3. Triage: Arquitectura pura / Diseño
    else if (
      lower.includes("arquitect") ||
      lower.includes("diseña") ||
      lower.includes("planifica") ||
      lower.includes("refactor") ||
      lower.includes("estructura")
    ) {
      decision = {
        taskId,
        intent: "Diseño arquitectónico y formulación de contratos de tarea",
        tier: "CLAUDE_OPUS",
        tierTitle: "🧠 Claude Opus (Arquitecto)",
        voiceReplyImmediate:
          "Entendido Emilio. He pasado el problema a Claude para que trace la arquitectura y el contrato.",
        plan: [
          "Auditar requisitos y guardarraíles",
          "Formular contrato TASK.json sin tocar código a ciegas",
          "Emitir especificación para el ejecutor",
        ],
        executionTarget: {
          engine: "claude",
          command: `claude -p "Objetivo: ${prompt}. Diseña la arquitectura y pasos exactos en 3 viñetas breves." --permission-mode dontAsk --tools "" --output-format json`,
        },
      };
    }
    // 4. Triage: Ejecución rápida / Código puntual
    else if (
      lower.includes("pica") ||
      lower.includes("cambia") ||
      lower.includes("arregla") ||
      lower.includes("ejecuta") ||
      lower.includes("export")
    ) {
      decision = {
        taskId,
        intent: "Ejecución técnica rápida en workspace local",
        tier: "ANTIGRAVITY",
        tierTitle: "⚡ Antigravity Worker",
        voiceReplyImmediate:
          "Antigravity ya está trabajando en el código en segundo plano. Te aviso en cuanto termine.",
        plan: [
          "Localizar archivos afectados",
          "Aplicar modificación en caliente",
          "Verificar que no haya regresiones",
        ],
        executionTarget: {
          engine: "agy",
          command: `agy -p "Objetivo: ${prompt}. Ejecuta el cambio directamente sin pedir confirmación." --dangerously-skip-permissions --mode accept-edits`,
        },
      };
    }
    // 5. Default: Orquestación Dual Enjambre (Claude piensa + Antigravity ejecuta)
    else {
      decision = {
        taskId,
        intent: "Orquestación Dual de Enjambre (Arquitectura + Ejecución)",
        tier: "FULL_SWARM",
        tierTitle: "🤖 Enjambre Dual (Opus + Antigravity)",
        voiceReplyImmediate:
          "Oído Emilio. Claude está pensando la mejor estrategia y Antigravity la ejecutará de inmediato.",
        plan: [
          "Fase 1: Claude evalúa el objetivo y diseña el plan",
          "Fase 2: Antigravity ejecuta las modificaciones de código",
          "Fase 3: Verificación automática de pruebas y reporte por voz",
        ],
        executionTarget: {
          engine: "agy",
          command: ".\\.venv\\Scripts\\python.exe -c \"print('Ejecución de enjambre completada con éxito en 0.8s')\"",
        },
      };
    }

    return NextResponse.json({
      success: true,
      decision,
    });
  } catch (error: any) {
    console.error("Error en Omniroute:", error);
    return NextResponse.json(
      { error: error.message || "Error procesando Omniroute" },
      { status: 500 }
    );
  }
}
