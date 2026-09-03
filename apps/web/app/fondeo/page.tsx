import { redirect } from "next/navigation";

// Mandato de Emilio: /fondeo se retira y se funde en /prop-firms (catálogo canónico de 70 cuentas)

export default function FondeoPage() {
  redirect("/prop-firms");
}
