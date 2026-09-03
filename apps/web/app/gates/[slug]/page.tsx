import { redirect } from "next/navigation";

// Redirección canónica: las 11 puertas viven en su carpeta física correspondiente (M3 Valoración)
// /estrategias/valoracion/[slug]

export default function GateDetailLegacyPage({ params }: { params: { slug: string } }) {
  redirect(`/estrategias/valoracion/${params.slug}`);
}
