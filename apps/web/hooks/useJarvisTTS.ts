"use client";

import { useState, useRef, useCallback } from "react";

export interface DeepgramVoiceOption {
  id: string;
  name: string;
  description: string;
}

export const DEEPGRAM_SPANISH_VOICES: DeepgramVoiceOption[] = [
  {
    id: "deepgram/aura-2-alvaro-es",
    name: "Álvaro (Jarvis)",
    description: "Calmado, seguro y cercano · Ideal asistente ejecutivo",
  },
  {
    id: "deepgram/aura-2-silvia-es",
    name: "Silvia",
    description: "Cálida, empática y natural",
  },
  {
    id: "deepgram/aura-2-nestor-es",
    name: "Néstor",
    description: "Sereno, técnico y profesional",
  },
];

export function useJarvisTTS() {
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [currentVoice, setCurrentVoice] = useState<string>("deepgram/aura-2-alvaro-es");
  const [provider, setProvider] = useState<"deepgram" | "browser">("deepgram");

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const currentBlobUrlRef = useRef<string | null>(null);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (currentBlobUrlRef.current) {
      URL.revokeObjectURL(currentBlobUrlRef.current);
      currentBlobUrlRef.current = null;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, []);

  const speakWithBrowserFallback = useCallback(
    (text: string, onEnd?: () => void) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) {
        if (onEnd) onEnd();
        return;
      }
      stop();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "es-ES";
      utterance.rate = 1.05;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => {
        setIsSpeaking(false);
        if (onEnd) onEnd();
      };
      utterance.onerror = () => {
        setIsSpeaking(false);
        if (onEnd) onEnd();
      };
      window.speechSynthesis.speak(utterance);
    },
    [stop]
  );

  const speak = useCallback(
    async (text: string, onEnd?: () => void) => {
      if (isMuted || !text.trim()) {
        if (onEnd) onEnd();
        return;
      }

      stop();
      setIsSpeaking(true);

      try {
        // 1. Intentar síntesis con Deepgram Aura-2 vía API
        const res = await fetch("/api/jarvis/speech", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text,
            model: currentVoice,
          }),
        });

        if (!res.ok) {
          throw new Error(`Fallo HTTP ${res.status} al sintetizar voz con Deepgram`);
        }

        const audioBlob = await res.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        currentBlobUrlRef.current = audioUrl;

        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        audio.onended = () => {
          setIsSpeaking(false);
          if (currentBlobUrlRef.current) {
            URL.revokeObjectURL(currentBlobUrlRef.current);
            currentBlobUrlRef.current = null;
          }
          if (onEnd) onEnd();
        };

        audio.onerror = (e) => {
          console.warn("Error reproduciendo audio Deepgram:", e);
          speakWithBrowserFallback(text, onEnd);
        };

        await audio.play();
        setProvider("deepgram");
      } catch (err) {
        console.warn("Deepgram offline o falló, recurriendo al sintetizador local:", err);
        setProvider("browser");
        speakWithBrowserFallback(text, onEnd);
      }
    },
    [isMuted, currentVoice, stop, speakWithBrowserFallback]
  );

  const speakFiller = useCallback(
    (type: "thinking" | "orchestrating" | "executing") => {
      const fillers = {
        thinking: [
          "Entendido Emilio, analizando la orden.",
          "Oído, procesando la solicitud.",
        ],
        orchestrating: [
          "Pasando la arquitectura a Claude para diseñar el plan.",
          "Coordinando el contrato con Claude Code.",
        ],
        executing: [
          "Antigravity ya está trabajando en segundo plano.",
          "Lanzando los subagentes de ejecución.",
        ],
      };

      const options = fillers[type] || fillers.thinking;
      const chosen = options[Math.floor(Math.random() * options.length)];
      speak(chosen);
    },
    [speak]
  );

  const toggleMute = useCallback(() => {
    setIsMuted((prev) => {
      if (!prev) stop();
      return !prev;
    });
  }, [stop]);

  return {
    speak,
    speakFiller,
    stop,
    isSpeaking,
    isMuted,
    toggleMute,
    currentVoice,
    setCurrentVoice,
    availableVoices: DEEPGRAM_SPANISH_VOICES,
    provider,
  };
}
