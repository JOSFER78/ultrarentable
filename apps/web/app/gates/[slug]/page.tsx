import React from "react";
import GateDetailClient, { ALL_GATES } from "./GateDetailClient";

export function generateStaticParams() {
  return ALL_GATES.map((g) => ({ slug: g.slug }));
}

export default function GateDetailPage() {
  return <GateDetailClient />;
}
