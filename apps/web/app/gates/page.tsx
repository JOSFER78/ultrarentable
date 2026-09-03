import { redirect } from "next/navigation";

// Mandato de arquitectura: Gates se funde canónicamente en M3 Valoración
// (/estrategias/valoracion)

export default function GatesRedirectPage() {
  redirect("/estrategias/valoracion");
}
