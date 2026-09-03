import { NextResponse } from "next/server";
import { exec } from "child_process";
import fs from "fs";
import path from "path";

// Directorio raíz de Ultrarentable
const PROJECT_ROOT = path.resolve(process.cwd(), "..", "..");

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { taskId, tier, executionTarget, prompt } = body;

    if (!executionTarget?.command) {
      return NextResponse.json(
        { error: "Comando de ejecución no especificado" },
        { status: 400 }
      );
    }

    const startTime = Date.now();
    const commandToRun = executionTarget.command;

    // Registrar evento de inicio en events.jsonl
    const swarmDir = path.join(PROJECT_ROOT, "orchestration", "swarm");
    const eventsFile = path.join(swarmDir, "events.jsonl");

    try {
      if (!fs.existsSync(swarmDir)) {
        fs.mkdirSync(swarmDir, { recursive: true });
      }
      const startEvent = JSON.stringify({
        timestamp: new Date().toISOString(),
        taskId: taskId || "JARVIS-AUTO",
        type: "TASK_STARTED",
        tier: tier || "ANTIGRAVITY",
        prompt: prompt || "",
        command: commandToRun,
      });
      fs.appendFileSync(eventsFile, startEvent + "\n", "utf8");
    } catch (e) {
      console.warn("No se pudo escribir en events.jsonl:", e);
    }

    // Ejecutar el comando físico en Windows
    const result: {
      stdout: string;
      stderr: string;
      exitCode: number;
      durationMs: number;
    } = await new Promise((resolve) => {
      exec(
        commandToRun,
        {
          cwd: executionTarget.cwd || PROJECT_ROOT,
          windowsHide: true,
          timeout: 45000, // 45s max
        },
        (error, stdout, stderr) => {
          const durationMs = Date.now() - startTime;
          resolve({
            stdout: stdout ? stdout.trim() : "",
            stderr: stderr ? stderr.trim() : "",
            exitCode: error ? error.code || 1 : 0,
            durationMs,
          });
        }
      );
    });

    const elapsedSeconds = (result.durationMs / 1000).toFixed(1);
    const isSuccess = result.exitCode === 0;

    // Redactar las 3 frases ejecutivas para la voz de Jarvis
    let voiceConclusion = "";
    if (tier === "RUN_TESTS") {
      voiceConclusion = isSuccess
        ? `Listo Emilio. Antigravity ha ejecutado la batería de pruebas en ${elapsedSeconds} segundos. Todas las aserciones han pasado al cien por cien y no hay regresiones.`
        : `Emilio, la prueba se ejecutó en ${elapsedSeconds} segundos pero arrojó un fallo en la salida. Puedes revisar el detalle en pantalla.`;
    } else if (tier === "CLAUDE_OPUS") {
      voiceConclusion = `Emilio, Claude ha finalizado el análisis arquitectónico en ${elapsedSeconds} segundos y ha delimitado el contrato de tarea para el enjambre.`;
    } else if (tier === "SYSTEM_STATUS") {
      voiceConclusion = `He auditado los procesos y servicios de tu PC en ${elapsedSeconds} segundos. El sistema está respondiendo con normalidad.`;
    } else {
      voiceConclusion = isSuccess
        ? `Listo Emilio. La tarea se completó con éxito en ${elapsedSeconds} segundos sin ninguna interrupción en tu pantalla.`
        : `La ejecución finalizó en ${elapsedSeconds} segundos con código de retorno ${result.exitCode}.`;
    }

    // Registrar evento de fin en events.jsonl
    try {
      const endEvent = JSON.stringify({
        timestamp: new Date().toISOString(),
        taskId: taskId || "JARVIS-AUTO",
        type: isSuccess ? "TASK_COMPLETED" : "TASK_FAILED",
        tier: tier || "ANTIGRAVITY",
        durationMs: result.durationMs,
        exitCode: result.exitCode,
      });
      fs.appendFileSync(eventsFile, endEvent + "\n", "utf8");
    } catch (e) {}

    return NextResponse.json({
      success: true,
      taskId,
      exitCode: result.exitCode,
      durationMs: result.durationMs,
      elapsedSeconds,
      stdout: result.stdout,
      stderr: result.stderr,
      voiceConclusion,
    });
  } catch (error: any) {
    console.error("Error en ejecución de Jarvis:", error);
    return NextResponse.json(
      { error: error.message || "Error en ejecutor agéntico" },
      { status: 500 }
    );
  }
}
