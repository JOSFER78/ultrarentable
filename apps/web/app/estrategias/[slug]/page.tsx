import React from "react";
import DynamicEstrategiasSlugClient from "./DynamicEstrategiasSlugClient";

export function generateStaticParams() {
  return [
    { slug: "0-portada" },
    { slug: "1-motor-247-telemetria" },
    { slug: "2-catalogo-candidatos-familias" },
    { slug: "3-fsm-candidatos" },
    { slug: "4-investigacion-fallos" },
    { slug: "5-estrategias-aprobadas" },
    { slug: "6-meta-estrategias-portfolio" },
  ];
}

export default function DynamicEstrategiasSlugPage() {
  return <DynamicEstrategiasSlugClient />;
}
