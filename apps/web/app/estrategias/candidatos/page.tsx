import { obtenerCensoData } from "@/lib/censoServer";
import CandidatosPageClient from "@/components/candidatos/CandidatosPageClient";

export const dynamic = "force-dynamic";

export default async function PaginaCandidatosM4() {
  const initialCenso = await obtenerCensoData();
  return <CandidatosPageClient initialCenso={initialCenso} />;
}
