"use client";

import React, { useRef, useState, useEffect } from "react";

export type JarvisAnimState =
  | "idle"
  | "listening"
  | "thinking"
  | "orchestrating"
  | "executing"
  | "success"
  | "error";

interface JarvisPetProps {
  animState: JarvisAnimState;
  scale?: number;
  className?: string;
  onClick?: () => void;
}

export const JarvisPet: React.FC<JarvisPetProps> = ({
  animState = "idle",
  scale = 1,
  className = "",
  onClick,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });

  // Seguimiento suave del ratón (LERP)
  useEffect(() => {
    let raf: number;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const onMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.hypot(dx, dy);
      const angle = Math.atan2(dy, dx);
      const maxR = 4.5;
      const clamped = Math.min(dist * 0.02, maxR);
      targetX = clamped * Math.cos(angle);
      targetY = clamped * Math.sin(angle);
    };

    const loop = () => {
      currentX += (targetX - currentX) * 0.12;
      currentY += (targetY - currentY) * 0.12;
      setEyeOffset({ x: currentX, y: currentY });
      raf = requestAnimationFrame(loop);
    };

    window.addEventListener("mousemove", onMove);
    loop();
    return () => {
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(raf);
    };
  }, []);

  const size = 80 * scale;

  // Colores dinámicos según estado
  const stateColors = {
    idle: "#00F0FF", // Cyan futurista
    listening: "#10B981", // Verde esmeralda escucha
    thinking: "#F59E0B", // Ámbar dorado reflexión
    orchestrating: "#3B82F6", // Azul Claude Opus
    executing: "#8B5CF6", // Violeta Antigravity
    success: "#22C55E", // Verde brillante éxito
    error: "#EF4444", // Rojo alerta
  };

  const currentColor = stateColors[animState] || stateColors.idle;

  const isThinking = animState === "thinking";
  const isOrchestrating = animState === "orchestrating";
  const isExecuting = animState === "executing";
  const isListening = animState === "listening";
  const isSuccess = animState === "success";

  return (
    <div
      ref={containerRef}
      style={{
        width: size,
        height: size,
        filter: `drop-shadow(0 0 ${10 * scale}px ${currentColor}80)`,
        transition: "width 0.3s ease, height 0.3s ease, filter 0.3s ease",
      }}
      className={`select-none relative flex items-center justify-center cursor-pointer ${className}`}
      onClick={onClick}
    >
      {/* Halo energético pulsante detrás */}
      <div
        className="absolute inset-0 rounded-full blur-2xl animate-pulse opacity-40 pointer-events-none transition-colors duration-500"
        style={{ background: currentColor }}
      />

      {/* SVG del Pet Animado */}
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full relative z-10"
        style={{
          animation:
            isExecuting
              ? "petExec 1.2s ease-in-out infinite"
              : isListening
              ? "petListen 1.5s ease-in-out infinite"
              : "petBounce 2.5s ease-in-out infinite, petBreath 3s ease-in-out infinite",
        }}
      >
        <style>{`
          @keyframes petBounce {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-5px); }
          }
          @keyframes petBreath {
            0%, 100% { transform: scaleY(1); }
            50% { transform: scaleY(1.03); }
          }
          @keyframes petListen {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.06); }
          }
          @keyframes petExec {
            0%, 100% { transform: translateY(0px) rotate(0deg); }
            25% { transform: translateY(-3px) rotate(1deg); }
            75% { transform: translateY(-3px) rotate(-1deg); }
          }
          @keyframes blink {
            0%, 90%, 100% { transform: scaleY(1); }
            95% { transform: scaleY(0.1); }
          }
          @keyframes orbitSlow {
            0% { transform: rotate(0deg) translateX(24px) rotate(0deg); }
            100% { transform: rotate(360deg) translateX(24px) rotate(-360deg); }
          }
          @keyframes orbitFast {
            0% { transform: rotate(360deg) translateX(20px) rotate(-360deg); }
            100% { transform: rotate(0deg) translateX(20px) rotate(0deg); }
          }
          @keyframes pulseAntenna {
            0%, 100% { r: 4px; opacity: 0.8; }
            50% { r: 6px; opacity: 1; }
          }
          @keyframes soundWave {
            0%, 100% { height: 4px; }
            50% { height: 14px; }
          }
        `}</style>

        {/* 1. Antena Superior */}
        <line
          x1="50"
          y1="26"
          x2="50"
          y2="14"
          stroke={currentColor}
          strokeWidth="3"
          strokeLinecap="round"
          className="transition-colors duration-300"
        />
        <circle
          cx="50"
          cy="11"
          r="4.5"
          fill={currentColor}
          style={{
            animation: "pulseAntenna 1.5s ease-in-out infinite",
          }}
          className="transition-colors duration-300"
        />

        {/* 2. Orejas / Sensores laterales */}
        <rect
          x="16"
          y="38"
          width="8"
          height="16"
          rx="3"
          fill={currentColor}
          opacity="0.85"
          className="transition-colors duration-300"
        />
        <rect
          x="76"
          y="38"
          width="8"
          height="16"
          rx="3"
          fill={currentColor}
          opacity="0.85"
          className="transition-colors duration-300"
        />

        {/* 3. Chasis / Cabeza del Robot */}
        <rect
          x="24"
          y="26"
          width="52"
          height="44"
          rx="14"
          fill="#0B1320"
          stroke={currentColor}
          strokeWidth="2.5"
          className="transition-colors duration-300"
        />

        {/* 4. Visor Frontal Oscuro */}
        <rect
          x="30"
          y="32"
          width="40"
          height="24"
          rx="8"
          fill="#050B14"
          stroke="#1E293B"
          strokeWidth="1"
        />

        {/* 5. Ojos Digitales con Tracking LERP */}
        {!isSuccess ? (
          <>
            {/* Ojo Izquierdo */}
            <circle
              cx={42 + eyeOffset.x}
              cy={44 + eyeOffset.y}
              r="5"
              fill={currentColor}
              style={{
                animation: "blink 4s ease-in-out infinite",
                transformOrigin: "42px 44px",
              }}
              className="transition-colors duration-300"
            />
            {/* Ojo Derecho */}
            <circle
              cx={58 + eyeOffset.x}
              cy={44 + eyeOffset.y}
              r="5"
              fill={currentColor}
              style={{
                animation: "blink 4s ease-in-out infinite 0.05s",
                transformOrigin: "58px 44px",
              }}
              className="transition-colors duration-300"
            />
            {/* Brillos especulares */}
            <circle
              cx={40.5 + eyeOffset.x}
              cy={42.5 + eyeOffset.y}
              r="1.6"
              fill="#FFFFFF"
              opacity="0.9"
            />
            <circle
              cx={56.5 + eyeOffset.x}
              cy={42.5 + eyeOffset.y}
              r="1.6"
              fill="#FFFFFF"
              opacity="0.9"
            />
          </>
        ) : (
          /* Ojos sonrientes en modo éxito */
          <>
            <path
              d="M 38 45 Q 42 40 46 45"
              stroke="#22C55E"
              strokeWidth="2.5"
              strokeLinecap="round"
              fill="none"
            />
            <path
              d="M 54 45 Q 58 40 62 45"
              stroke="#22C55E"
              strokeWidth="2.5"
              strokeLinecap="round"
              fill="none"
            />
          </>
        )}

        {/* 6. Boca / Ecualizador animado */}
        {isListening ? (
          /* Ondas de audio al escuchar */
          <g transform="translate(42, 58)">
            <rect
              x="0"
              y="0"
              width="2.5"
              height="8"
              rx="1"
              fill="#10B981"
              style={{ animation: "soundWave 0.5s ease-in-out infinite" }}
            />
            <rect
              x="5"
              y="-2"
              width="2.5"
              height="12"
              rx="1"
              fill="#10B981"
              style={{
                animation: "soundWave 0.7s ease-in-out infinite 0.1s",
              }}
            />
            <rect
              x="10"
              y="-4"
              width="2.5"
              height="16"
              rx="1"
              fill="#10B981"
              style={{
                animation: "soundWave 0.4s ease-in-out infinite 0.2s",
              }}
            />
            <rect
              x="15"
              y="0"
              width="2.5"
              height="8"
              rx="1"
              fill="#10B981"
              style={{
                animation: "soundWave 0.6s ease-in-out infinite 0.15s",
              }}
            />
          </g>
        ) : (
          <rect
            x="44"
            y="58"
            width="12"
            height={isExecuting || isOrchestrating ? "3.5" : "2"}
            rx="1"
            fill={currentColor}
            opacity="0.9"
            className="transition-colors duration-300"
          />
        )}

        {/* 7. Propulsor inferior con estela energética */}
        <polygon
          points="42,70 58,70 50,80"
          fill={currentColor}
          opacity="0.65"
          className="transition-colors duration-300"
        />

        {/* 8. Partículas Orbitales (Pensando / Orquestando) */}
        {(isThinking || isOrchestrating) && (
          <g>
            <circle
              cx="50"
              cy="44"
              r="3.5"
              fill="#F59E0B"
              style={{
                animation: "orbitSlow 1.4s linear infinite",
                transformOrigin: "50px 44px",
              }}
            />
            <circle
              cx="50"
              cy="44"
              r="2.5"
              fill="#3B82F6"
              style={{
                animation: "orbitFast 1.1s linear infinite",
                transformOrigin: "50px 44px",
              }}
            />
          </g>
        )}

        {/* 9. Anillo de Ejecución Agéntica (Antigravity) */}
        {isExecuting && (
          <circle
            cx="50"
            cy="48"
            r="38"
            fill="none"
            stroke="#8B5CF6"
            strokeWidth="2"
            strokeDasharray="8 6"
            style={{
              animation: "spinRing 2s linear infinite",
              transformOrigin: "50px 48px",
            }}
          />
        )}
      </svg>
    </div>
  );
};
