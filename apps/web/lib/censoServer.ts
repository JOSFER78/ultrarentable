import { EstrategiaRow } from "@/components/estrategias/EstrategiasComparativaTable";

export interface CensoServerData {
  status: string;
  estrategias: EstrategiaRow[];
  fondeo_total: number;
  otros_proyectos: number;
  otros_sin_metricas: number;
  candidatos_evaluados: number;
  aviso_otros: string;
  detalle_celdas: Array<{
    celda: string;
    extraidas_en_censo: number;
    en_banco_servidor: number;
    generadas_servidor?: number;
    aceptado_pct?: number;
    etiqueta: string;
  }>;
}

export async function obtenerCensoData(): Promise<CensoServerData> {
  const backendUrl =
    process.env.BACKEND_URL ||
    process.env.ULTRARENTABLE_API_URL ||
    "http://127.0.0.1:8100";

  try {
    const res = await fetch(`${backendUrl}/api/v2/candidates/censo?limite=1000`, {
      cache: "no-store",
    });
    if (res.ok) {
      const data = await res.json();
      return data as CensoServerData;
    }
  } catch (err) {
    console.error("Error al obtener censo desde backend en SSR:", err);
  }

  return {
    status: "ERROR",
    estrategias: [],
    fondeo_total: 0,
    otros_proyectos: 0,
    otros_sin_metricas: 0,
    candidatos_evaluados: 0,
    aviso_otros: "No se pudo conectar con el backend local",
    detalle_celdas: [],
  };
}
