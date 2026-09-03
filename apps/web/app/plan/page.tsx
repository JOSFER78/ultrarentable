/**
 * apps/web/app/plan/page.tsx
 *
 * Página /plan (Server Component). Lee el tablero de tareas orchestration/tablero/*.md
 * en el servidor para renderizado estático inicial (SSR completo auditable por curl/browser)
 * y pasa el estado a PlanPageClient.
 */

import { obtenerTableroData } from "@/lib/tableroServer";
import PlanPageClient from "@/components/plan/PlanPageClient";

export const dynamic = "force-dynamic";

export default function PlanPage() {
  const initialTablero = obtenerTableroData();
  return <PlanPageClient initialTablero={initialTablero} />;
}
