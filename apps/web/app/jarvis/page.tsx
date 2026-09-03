"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  VolumeX,
  Sparkles,
  Terminal,
  Cpu,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldAlert,
  Layers,
  Zap,
} from "lucide-react";
import { JarvisPet, JarvisAnimState } from "@/components/jarvis/JarvisPet";
import { useJarvisTTS } from "@/hooks/useJarvisTTS";

export default function JarvisCockpitPage() {
  const [animState, setAnimState] = useState<JarvisAnimState>("idle");
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [inputText, setInputText] = useState<string>("");
  const [transcript, setTranscript] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<string>("");
  const [omnirouteDecision, setOmnirouteDecision] = useState<any>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);

  const { speak, speakFiller, stop: stopSpeech, isSpeaking, isMuted, toggleMute } =
    useJarvisTTS();

  const recognitionRef = useRef<any>(null);

  const startVoice = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "es-ES";
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        setIsRecording(true);
        setAnimState("listening");
      };

      recognition.onresult = (event: any) => {
        let current = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          current += event.results[i][0].transcript;
        }
        setTranscript(current.trim());
        setInputText(current.trim());
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (!isProcessing) setAnimState("idle");
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.warn("Speech error:", e);
    }
  };

  const stopVoice = () => {
    setIsRecording(false);
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
      recognitionRef.current = null;
    }
  };

  const handleDispatch = async (promptToSend?: string) => {
    const finalPrompt = (promptToSend || inputText || transcript).trim();
    if (!finalPrompt || isProcessing) return;

    stopVoice();
    setIsProcessing(true);
    setAnimState("thinking");
    setActiveStep("Omniroute analizando intención...");
    speakFiller("thinking");
    setOmnirouteDecision(null);
    setExecutionResult(null);

    try {
      // 1. Omniroute Triage
      const routeRes = await fetch("/api/jarvis/omniroute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: finalPrompt }),
      });

      const routeData = await routeRes.json();
      if (!routeData.success) {
        throw new Error(routeData.error || "Error en Omniroute");
      }

      const decision = routeData.decision;
      setOmnirouteDecision(decision);

      if (decision.tier === "CLAUDE_OPUS") {
        setAnimState("orchestrating");
        setActiveStep("Claude Opus formulando arquitectura...");
        speakFiller("orchestrating");
      } else {
        setAnimState("executing");
        setActiveStep(decision.tierTitle + " ejecutando...");
        speakFiller("executing");
      }

      // 2. Ejecución Agéntica
      const execRes = await fetch("/api/jarvis/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          taskId: decision.taskId,
          tier: decision.tier,
          executionTarget: decision.executionTarget,
          prompt: finalPrompt,
        }),
      });

      const execData = await execRes.json();
      setExecutionResult(execData);

      if (execData.exitCode === 0) {
        setAnimState("success");
        setActiveStep(`¡Completado en ${execData.elapsedSeconds}s!`);
      } else {
        setAnimState("error");
        setActiveStep(`Completado con advertencia (${execData.elapsedSeconds}s)`);
      }

      if (execData.voiceConclusion) {
        speak(execData.voiceConclusion);
      }

      // Guardar en historial de la sesión
      setHistory((prev) => [
        {
          id: decision.taskId,
          prompt: finalPrompt,
          tier: decision.tierTitle,
          duration: execData.elapsedSeconds,
          success: execData.exitCode === 0,
          time: new Date().toLocaleTimeString(),
        },
        ...prev,
      ]);
    } catch (err: any) {
      setAnimState("error");
      setActiveStep("Fallo en la ejecución");
      speak("Emilio, ha habido una incidencia al ejecutar la orden.");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col p-4 md:p-8 max-w-7xl mx-auto w-full text-slate-100 font-sans space-y-6">
      
      {/* Cabecera de la Cabina */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              JARVIS COCKPIT & MISSION CONTROL
            </h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
              Omniroute v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Control de voz, orquestación con Claude Code y ejecución física con Antigravity.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={toggleMute}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono border flex items-center gap-2 transition-colors ${
              isMuted
                ? "bg-red-950/40 border-red-800 text-red-400"
                : "bg-slate-800 border-slate-700 text-slate-300 hover:text-white"
            }`}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            <span>{isMuted ? "Voz Silenciada" : "Voz Activa"}</span>
          </button>
        </div>
      </div>

      {/* Rejilla Principal */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        
        {/* Columna Izquierda: Avatar y Controles de Voz (7 Cols) */}
        <div className="lg:col-span-7 flex flex-col bg-[#080D18] border border-[#1E293B] rounded-2xl p-6 shadow-2xl relative overflow-hidden">
          
          {/* Avatar Interactivo Central */}
          <div className="flex flex-col items-center justify-center py-6 flex-1">
            <JarvisPet
              animState={animState}
              scale={2.2}
              onClick={() => {
                if (isRecording) stopVoice();
                else startVoice();
              }}
            />

            {/* Badge de Estado Dinámico */}
            <div className="mt-6 text-center">
              <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-mono font-medium bg-[#0D1527] border border-[#1E2E4E] text-cyan-300 shadow-lg">
                {isProcessing ? (
                  <>
                    <Sparkles className="w-4 h-4 text-amber-400 animate-spin" />
                    {activeStep}
                  </>
                ) : isRecording ? (
                  <>
                    <Mic className="w-4 h-4 text-emerald-400 animate-pulse" />
                    Escuchando tu voz, Emilio…
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Jarvis en reposo · Esperando órdenes
                  </>
                )}
              </span>
            </div>
          </div>

          {/* Tarjeta de Dictamen de Jarvis */}
          {executionResult?.voiceConclusion && (
            <div className="mb-4 bg-[#0D172A] border border-cyan-800/60 rounded-xl p-4 flex items-start gap-3 animate-in fade-in duration-300">
              <Volume2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
              <div className="text-xs leading-relaxed text-slate-200">
                <span className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 block mb-1">
                  Respuesta de Jarvis:
                </span>
                {executionResult.voiceConclusion}
              </div>
            </div>
          )}

          {/* Barra de Entrada de Voz / Teclado */}
          <div className="pt-4 border-t border-slate-800/80 flex items-center gap-3">
            <button
              onClick={() => {
                if (isRecording) stopVoice();
                else startVoice();
              }}
              className={`p-3.5 rounded-xl border transition-all flex items-center justify-center shrink-0 ${
                isRecording
                  ? "bg-emerald-500 border-emerald-400 text-black shadow-lg shadow-emerald-500/20 animate-pulse"
                  : "bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700"
              }`}
            >
              {isRecording ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
            </button>

            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleDispatch();
              }}
              placeholder={
                isRecording
                  ? "Escuchando dictado de voz..."
                  : "Escribe o dicta tu orden a Jarvis..."
              }
              className="flex-1 bg-[#050912] border border-slate-800 focus:border-cyan-500 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 outline-none transition-all"
            />

            <button
              onClick={() => handleDispatch()}
              disabled={!inputText.trim() || isProcessing}
              className="p-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white transition-all shrink-0 flex items-center justify-center shadow-lg shadow-cyan-600/20"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>

          {/* Botones de Acción Inmediata */}
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              onClick={() => handleDispatch("Comprueba si los tests están pasando")}
              className="text-[11px] font-mono px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <Zap className="w-3 h-3 text-cyan-400" />
              <span>Ejecutar tests</span>
            </button>
            <button
              onClick={() => handleDispatch("Audita el estado de los procesos y puertos")}
              className="text-[11px] font-mono px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <Cpu className="w-3 h-3 text-emerald-400" />
              <span>Auditar PC</span>
            </button>
            <button
              onClick={() => handleDispatch("Diseña la arquitectura para el enjambre")}
              className="text-[11px] font-mono px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
            >
              <Layers className="w-3 h-3 text-blue-400" />
              <span>Plan con Claude</span>
            </button>
          </div>
        </div>

        {/* Columna Derecha: Omniroute Live & Terminal Cruda (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          
          {/* Panel Omniroute */}
          <div className="bg-[#080D18] border border-[#1E293B] rounded-2xl p-5 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-semibold text-white mb-3">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>DESGLOSE OMNIROUTE EN TIEMPO REAL</span>
            </div>

            {omnirouteDecision ? (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-xl bg-[#0D1527] border border-[#1E2E4E]">
                  <span className="text-[10px] uppercase font-mono text-slate-400 block">
                    Intención Detectada:
                  </span>
                  <span className="font-semibold text-white">
                    {omnirouteDecision.intent}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">Motor Asignado:</span>
                    <span className="text-cyan-400 font-bold">{omnirouteDecision.tierTitle}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-500 block">ID Tarea:</span>
                    <span className="text-slate-300">{omnirouteDecision.taskId}</span>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
                    Plan de Acción Ejecutado:
                  </span>
                  <ul className="space-y-1">
                    {omnirouteDecision.plan?.map((step: string, idx: number) => (
                      <li key={idx} className="flex items-start gap-2 text-[11px] text-slate-300">
                        <ArrowRight className="w-3 h-3 text-cyan-500 shrink-0 mt-0.5" />
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-slate-500 text-xs font-mono">
                Dicta o escribe una orden para ver la resolución de Omniroute.
              </div>
            )}
          </div>

          {/* Salida de Terminal Cruda */}
          <div className="bg-[#080D18] border border-[#1E293B] rounded-2xl p-5 shadow-xl flex-1 flex flex-col">
            <div className="flex items-center justify-between text-xs font-semibold text-white mb-2">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-emerald-400" />
                <span>SALIDA TÉCNICA (TERMINAL LOCAL)</span>
              </div>
              {executionResult && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  exit code: {executionResult.exitCode}
                </span>
              )}
            </div>

            <div className="flex-1 min-h-[160px] bg-black/90 rounded-xl p-3 border border-slate-800 font-mono text-[11px] text-emerald-400 overflow-y-auto max-h-64 whitespace-pre-wrap">
              {executionResult?.stdout ? (
                <>
                  {executionResult.stdout}
                  {executionResult.stderr && (
                    <span className="text-red-400 block mt-2">
                      {executionResult.stderr}
                    </span>
                  )}
                </>
              ) : isProcessing ? (
                <span className="text-amber-400 animate-pulse">
                  Ejecutando proceso en Windows en segundo plano...
                </span>
              ) : (
                <span className="text-slate-600">
                  Esperando ejecución para capturar salida de terminal.
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
