import React from "react";
import GateDetailClient from "./GateDetailClient";

// Sin generateStaticParams: ALL_GATES vive en un modulo "use client" y en build llega como
// client-reference (llamar .map() ahi rompe `next build`). La ruta se renderiza bajo demanda.

export default function GateDetailPage() {
  return <GateDetailClient />;
}
