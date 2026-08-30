"use client";

import SistemaSupervisorPage from "@/app/sistema/page";
import EstrategiasHeaderNav from "@/components/EstrategiasHeaderNav";

export default function MotorEnVivoPage() {
  return (
    <div className="min-h-screen bg-[#030712] p-3 md:p-6 font-sans text-slate-100 space-y-5">
      <div className="max-w-[1600px] mx-auto space-y-5">
        <EstrategiasHeaderNav currentPhase={1} />
        <SistemaSupervisorPage />
      </div>
    </div>
  );
}