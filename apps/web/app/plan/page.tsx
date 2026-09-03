/**
 * apps/web/app/plan/page.tsx
 *
 * Página /plan (Server Component). Lee el plan por fases (F00..F10) con avance calculado
 * y el tablero de tareas (A01..A43) en el servidor para SSR completo (auditable por curl/browser)
 * y pasa los datos iniciales a PlanPageClient.
 */

import { obtenerTableroData } from "@/lib/tableroServer";
import { obtenerFasesPlanData } from "@/lib/fasesServer";
import PlanPageClient from "@/components/plan/PlanPageClient";

export const dynamic = "force-dynamic";

export default function PlanPage() {
  const initialTablero = obtenerTableroData();
  const initialFases = obtenerFasesPlanData();
  return <PlanPageClient initialTablero={initialTablero} initialFases={initialFases} />;
}
