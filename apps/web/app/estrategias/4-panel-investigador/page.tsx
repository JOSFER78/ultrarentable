"use client";

import ResearchLabPage from "@/app/research/page";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

export default function PanelInvestigadorPage() {
  return (
    <div className="min-h-screen bg-[#030712] p-3 md:p-6 font-sans text-slate-100 space-y-5">
      <div className="max-w-[1600px] mx-auto space-y-5">
        <EstrategiasHeaderNav currentPhase={4} />
        <ResearchLabPage />
      </div>
    </div>
  );
}
