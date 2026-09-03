import { NextRequest } from "next/server";
import fs from "fs";
import path from "path";
import { findRepoRoot } from "@/lib/projectPaths";

export const dynamic = "force-dynamic";

export interface SwarmTaskData {
  task_id: string;
  phase?: string;
  title: string;
  objective?: string;
  scope_files?: string[];
  prohibited_actions?: string[];
  acceptance_criteria?: {
    command: string;
    expected_exit_code?: number;
  };
  status: "INITIALIZED" | "DISPATCHED" | "IN_PROGRESS" | "EXECUTED" | "VERIFIED" | "RETURNED";
  dispatched_at?: string;
}

export interface SwarmResultData {
  task_id: string;
  status: string;
  exit_code: number;
  execution_seconds?: number;
  files_modified?: string[];
  git_diff_summary?: string;
  test_raw_output?: string;
  findings_or_blockers?: string | null;
  executed_at?: string;
}

export interface SwarmSnapshot {
  timestamp: string;
  task: SwarmTaskData | null;
  result: SwarmResultData | null;
  active_subagents: Array<{ id: string; role: string; status: string }>;
  circuit_round: number;
  history_count: number;
}

export async function GET(req: NextRequest) {
  const encoder = new TextEncoder();
  const repoRoot = findRepoRoot();
  const swarmDir = path.join(repoRoot, "orchestration", "swarm");

  const stream = new ReadableStream({
    start(controller) {
      const buildSnapshot = (): SwarmSnapshot => {
        let task: SwarmTaskData | null = null;
        let result: SwarmResultData | null = null;
        let historyCount = 0;

        try {
          const taskPath = path.join(swarmDir, "TASK.json");
          if (fs.existsSync(taskPath)) {
            task = JSON.parse(fs.readFileSync(taskPath, "utf-8"));
          }
        } catch {
          task = null;
        }

        try {
          const resultPath = path.join(swarmDir, "RESULT.json");
          if (fs.existsSync(resultPath)) {
            result = JSON.parse(fs.readFileSync(resultPath, "utf-8"));
          }
        } catch {
          result = null;
        }

        try {
          const archiveDir = path.join(swarmDir, "archive");
          if (fs.existsSync(archiveDir)) {
            historyCount = fs.readdirSync(archiveDir).filter((f) => f.endsWith(".json")).length;
          }
        } catch {
          historyCount = 0;
        }

        return {
          timestamp: new Date().toISOString(),
          task,
          result,
          active_subagents: [
            { id: "A1", role: "Extractor / Minero", status: "Inactivo" },
            { id: "A2", role: "Auditor de Aceptación", status: "Listo" },
          ],
          circuit_round: 1,
          history_count: historyCount,
        };
      };

      const sendSnapshot = () => {
        try {
          const snap = buildSnapshot();
          controller.enqueue(encoder.encode(`event: snapshot\ndata: ${JSON.stringify(snap)}\n\n`));
        } catch {
          // Ignorar desconexiones de cliente cerradas
        }
      };

      // 1. Envío inicial de estado
      sendSnapshot();

      // 2. File Watcher nativo (cero tokens, reactivo a nivel de sistema de ficheros)
      let watcher: fs.FSWatcher | null = null;
      try {
        if (!fs.existsSync(swarmDir)) {
          fs.mkdirSync(swarmDir, { recursive: true });
        }
        watcher = fs.watch(swarmDir, (event, filename) => {
          if (filename && (filename.endsWith(".json") || filename.endsWith(".md"))) {
            sendSnapshot();
          }
        });
      } catch (err) {
        console.error("No se pudo iniciar el observador en tiempo real:", err);
      }

      // 3. Heartbeat cada 20 segundos para evitar timeouts de proxies
      const interval = setInterval(() => {
        try {
          controller.enqueue(encoder.encode(`: ping\n\n`));
        } catch {
          clearInterval(interval);
        }
      }, 20000);

      req.signal.addEventListener("abort", () => {
        if (watcher) watcher.close();
        clearInterval(interval);
        try {
          controller.close();
        } catch {
          // Controller cerrado
        }
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
    },
  });
}
