"use client";

import React, { useState, useEffect } from "react";
import { JarvisPet, JarvisAnimState } from "./JarvisPet";
import { JarvisVoiceModal } from "./JarvisVoiceModal";
import { Mic, Sparkles } from "lucide-react";

export const JarvisFloatingWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [animState, setAnimState] = useState<JarvisAnimState>("idle");
  const [showTooltip, setShowTooltip] = useState<boolean>(false);

  // Atajo de teclado: Alt + J para abrir Jarvis instantáneamente
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === "j" || e.key === "J")) {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      {/* Widget flotante en la esquina inferior derecha */}
      <div className="fixed bottom-5 right-5 z-[120] flex flex-col items-end">
        {/* Tooltip de saludo que aparece al pasar el ratón */}
        {showTooltip && !isOpen && (
          <div className="mb-2 px-3 py-1.5 rounded-xl bg-[#0B1324] border border-cyan-800 text-[11px] text-cyan-200 font-mono shadow-xl animate-in fade-in slide-in-from-bottom-2 duration-150 flex items-center gap-2">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>Pulsa o usa <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-[10px]">Alt+J</kbd> para hablar con Jarvis</span>
          </div>
        )}

        {/* Botón flotante con la mascota */}
        <div
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center justify-center p-2 rounded-2xl bg-[#090E1A]/90 hover:bg-[#0E172A] border border-cyan-500/30 hover:border-cyan-400/80 shadow-2xl backdrop-blur-md transition-all duration-300 hover:scale-105 cursor-pointer"
          style={{
            boxShadow: "0 8px 32px 0 rgba(0, 240, 255, 0.15)",
          }}
        >
          <JarvisPet animState={animState} scale={0.85} />
          
          {/* Pequeña insignia de micrófono */}
          <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border border-emerald-300 flex items-center justify-center text-black shadow-md group-hover:scale-110 transition-transform">
            <Mic className="w-3 h-3" />
          </div>
        </div>
      </div>

      {/* Modal de Control y Voz */}
      <JarvisVoiceModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
};
