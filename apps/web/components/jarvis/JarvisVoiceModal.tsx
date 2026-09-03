"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Mic,
  MicOff,
  X,
  Volume2,
  VolumeX,
  Send,
  Sparkles,
  Terminal,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Play,
  Clock,
  ArrowRight,
} from "lucide-react";
import { JarvisPet, JarvisAnimState } from "./JarvisPet";
import { useJarvisTTS } from "@/hooks/useJarvisTTS";

interface JarvisVoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const JarvisVoiceModal: React.FC<JarvisVoiceModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [animState, setAnimState] = useState<JarvisAnimState>("idle");
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [transcript, setTranscript] = useState<string>("");
  const [inputText, setInputText] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [activeStep, setActiveStep] = useState<string>("");
  const [omnirouteDecision, setOmnirouteDecision] = useState<any>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [showTerminal, setShowTerminal] = useState<boolean>(false);

  const {
    speak,
    speakFiller,
    stop: stopSpeech,
    isSpeaking,
    isMuted,
    toggleMute,
    currentVoice,
    setCurrentVoice,
    availableVoices,
    provider,
  } = useJarvisTTS();

  const recognitionRef = useRef<any>(null);

  // Iniciar / detener reconocimiento de voz
  useEffect(() => {
    if (!isOpen) {
      stopVoice();
      stopSpeech();
      setAnimState("idle");
      setIsProcessing(false);
      return;
    }

    startVoice();
    return () => {
      stopVoice();
    };
  }, [isOpen]);

  // Sincronizar estado visual con la locución
  useEffect(() => {
    if (isSpeaking && animState === "idle") {
      setAnimState("listening");
    }
  }, [isSpeaking]);

  const startVoice = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("SpeechRecognition no disponible en este navegador");
      return;
    }

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

      recognition.onerror = (e: any) => {
        console.warn("Error SpeechRecognition:", e);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
        if (!isProcessing) {
          setAnimState("idle");
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (e) {
      console.warn("Fallo al iniciar reconocimiento:", e);
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

  // Enviar orden al motor de Jarvis (Omniroute + Ejecución Agéntica)
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
      // 1. Fase Omniroute
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

      // Cambiar animación según el motor asignado
      if (decision.tier === "CLAUDE_OPUS") {
        setAnimState("orchestrating");
        setActiveStep("Claude Opus formulando arquitectura...");
        speakFiller("orchestrating");
      } else {
        setAnimState("executing");
        setActiveStep(decision.tierTitle + " ejecutando en tu PC...");
        speakFiller("executing");
      }

      // 2. Fase de Ejecución Agéntica Real
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

      // 3. Fase de Conclusión y Voz
      if (execData.exitCode === 0) {
        setAnimState("success");
        setActiveStep(`¡Completado con éxito en ${execData.elapsedSeconds}s!`);
      } else {
        setAnimState("error");
        setActiveStep(`Completado con advertencia (${execData.elapsedSeconds}s)`);
      }

      // Jarvis canta el resultado en voz alta
      if (execData.voiceConclusion) {
        speak(execData.voiceConclusion);
      }
    } catch (err: any) {
      console.error("Error en flujo de Jarvis:", err);
      setAnimState("error");
      setActiveStep("Ocurrió un problema en la ejecución");
      speak("Emilio, ha habido una incidencia al ejecutar la orden. Revisa los detalles en pantalla.");
    } finally {
      setIsProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-6">
      {/* Fondo desenfocado */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Contenedor del Modal */}
      <div className="relative z-10 w-full max-w-2xl bg-[#090D16] border border-[#1E293B] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] text-slate-100 font-sans animate-in zoom-in-95 duration-200">
        
        {/* Cabecera */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-[#1E293B] bg-[#0C1220]">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
            <div>
              <h2 className="text-sm font-semibold tracking-wide flex items-center gap-2 text-white">
                JARVIS COGNITIVE ASSISTANT
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  Omniroute MVP
                </span>
              </h2>
              <p className="text-[11px] text-slate-400">
                Orquestador Inteligente de Enjambre (Claude + Antigravity)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={toggleMute}
              className={`p-1.5 rounded-lg border transition-colors ${
                isMuted
                  ? "bg-red-950/40 border-red-800 text-red-400"
                  : "bg-slate-800/60 border-slate-700 text-slate-300 hover:text-white"
              }`}
              title={isMuted ? "Voz silenciada" : "Voz activa"}
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg bg-slate-800/60 border border-slate-700 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Cuerpo Principal */}
        <div className="p-5 flex-1 overflow-y-auto space-y-5">
          
          {/* Avatar Interactivo Central */}
          <div className="flex flex-col items-center justify-center py-2">
            <JarvisPet
              animState={animState}
              scale={1.4}
              onClick={() => {
                if (isRecording) stopVoice();
                else startVoice();
              }}
            />
            
            {/* Indicador de Estado Activo */}
            <div className="mt-3 text-center">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-[#0F172A] border border-[#334155] text-cyan-300">
                {isProcessing ? (
                  <>
                    <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                    {activeStep}
                  </>
                ) : isRecording ? (
                  <>
                    <Mic className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                    Te escucho, Emilio…
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    Listo para tus órdenes
                  </>
                )}
              </span>
            </div>
          </div>

          {/* Resultado de Omniroute & Ejecución Agéntica */}
          {omnirouteDecision && (
            <div className="bg-[#0B1324] border border-[#1E293B] rounded-xl p-4 space-y-3 animate-in fade-in duration-300">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-cyan-400" />
                  <span className="font-semibold text-white">
                    {omnirouteDecision.tierTitle}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">
                    ID: {omnirouteDecision.taskId}
                  </span>
                </div>
                {executionResult && (
                  <span
                    className={`inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded border ${
                      executionResult.exitCode === 0
                        ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
                        : "bg-red-950/60 border-red-800 text-red-300"
                    }`}
                  >
                    <Clock className="w-3 h-3" />
                    {executionResult.elapsedSeconds}s
                  </span>
                )}
              </div>

              {/* Dictamen hablado */}
              {executionResult?.voiceConclusion && (
                <div className="text-xs text-slate-200 bg-[#0F1B33] border border-cyan-900/60 rounded-lg p-3 leading-relaxed flex items-start gap-2.5">
                  <Volume2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 block mb-0.5">
                      Resumen Ejecutivo de Jarvis:
                    </span>
                    {executionResult.voiceConclusion}
                  </div>
                </div>
              )}

              {/* Toggle de Terminal Cruda */}
              {executionResult?.stdout && (
                <div>
                  <button
                    onClick={() => setShowTerminal(!showTerminal)}
                    className="text-[11px] text-slate-400 hover:text-cyan-300 flex items-center gap-1 font-mono transition-colors"
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    {showTerminal ? "Ocultar salida técnica" : "Ver salida técnica en crudo (Terminal)"}
                  </button>
                  {showTerminal && (
                    <pre className="mt-2 text-[11px] font-mono bg-black/80 text-emerald-400 border border-slate-800 rounded-lg p-3 max-h-48 overflow-y-auto whitespace-pre-wrap">
                      {executionResult.stdout}
                      {executionResult.stderr && (
                        <span className="text-red-400 block mt-2">
                          {executionResult.stderr}
                        </span>
                      )}
                    </pre>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Botones de Acción Rápida */}
          <div>
            <span className="text-[10px] uppercase tracking-wider font-mono text-slate-400 block mb-2">
              Órdenes Rápidas:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                onClick={() =>
                  handleDispatch("Comprueba si los tests están pasando")
                }
                disabled={isProcessing}
                className="text-left text-xs p-2.5 rounded-lg bg-[#0F172A] border border-[#1E293B] hover:border-cyan-500/50 hover:bg-[#131F38] text-slate-300 transition-all flex items-center justify-between group disabled:opacity-50"
              >
                <span>⚡ Ejecutar suite de tests con Antigravity</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              </button>

              <button
                onClick={() =>
                  handleDispatch("Audita el estado del sistema y procesos activos")
                }
                disabled={isProcessing}
                className="text-left text-xs p-2.5 rounded-lg bg-[#0F172A] border border-[#1E293B] hover:border-cyan-500/50 hover:bg-[#131F38] text-slate-300 transition-all flex items-center justify-between group disabled:opacity-50"
              >
                <span>👁️ Auditar estado y puertos de mi PC</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              </button>

              <button
                onClick={() =>
                  handleDispatch(
                    "Diseña la arquitectura para desacoplar el motor de exportación SQX"
                  )
                }
                disabled={isProcessing}
                className="text-left text-xs p-2.5 rounded-lg bg-[#0F172A] border border-[#1E293B] hover:border-cyan-500/50 hover:bg-[#131F38] text-slate-300 transition-all flex items-center justify-between group disabled:opacity-50"
              >
                <span>🧠 Planificar arquitectura con Claude Opus</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              </button>

              <button
                onClick={() =>
                  handleDispatch(
                    "Optimiza el flujo de datos para que tarde segundos y no día y medio"
                  )
                }
                disabled={isProcessing}
                className="text-left text-xs p-2.5 rounded-lg bg-[#0F172A] border border-[#1E293B] hover:border-cyan-500/50 hover:bg-[#131F38] text-slate-300 transition-all flex items-center justify-between group disabled:opacity-50"
              >
                <span>🤖 Orquestación Dual Enjambre Completa</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 transition-colors" />
              </button>
            </div>
          </div>
        </div>

        {/* Pie: Entrada de voz y teclado */}
        <div className="p-4 border-t border-[#1E293B] bg-[#0C1220] flex items-center gap-2.5">
          <button
            onClick={() => {
              if (isRecording) stopVoice();
              else startVoice();
            }}
            className={`p-3 rounded-xl border transition-all flex items-center justify-center shrink-0 ${
              isRecording
                ? "bg-emerald-500 border-emerald-400 text-black shadow-lg shadow-emerald-500/20 animate-pulse"
                : "bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700"
            }`}
            title={isRecording ? "Pausar micrófono" : "Activar micrófono"}
          >
            {isRecording ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
          </button>

          <div className="relative flex-1">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleDispatch();
              }}
              placeholder={
                isRecording
                  ? "Escuchando tu voz en tiempo real..."
                  : "O escribe aquí tu orden para Jarvis..."
              }
              className="w-full bg-[#070B14] border border-[#1E293B] focus:border-cyan-500 rounded-xl px-4 py-3 text-xs text-white placeholder-slate-500 outline-none transition-all"
            />
          </div>

          <button
            onClick={() => handleDispatch()}
            disabled={!inputText.trim() || isProcessing}
            className="p-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all shrink-0 flex items-center justify-center shadow-lg shadow-cyan-600/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
