/**
 * apps/web/app/api/tablero/route.ts
 *
 * El tablero de orquestación, leído en vivo de `orchestration/tablero/*.md`.
 */

import { NextResponse } from "next/server";
import { obtenerTableroData, ESTADOS_TABLERO } from "@/lib/tableroServer";

export const dynamic = "force-dynamic";

export { ESTADOS_TABLERO };
export type { EstadoTablero, TareaTablero } from "@/lib/tableroServer";

export async function GET() {
  const data = obtenerTableroData();
  return NextResponse.json(data);
}
