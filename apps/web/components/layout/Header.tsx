"use client";

/**
 * apps/web/components/layout/Header.tsx
 * Reescrito 2026-09-01 (AG-11, T3/T5 del contrato de poda web) conforme a
 * docs/19_UI_STYLE_SPEC.md §3 (Header): título de página + versión REAL del motor (dinámica,
 * leída de getDiscoveryStatus()) + estado de conexión API en gris (punto de 6px, verde si
 * operativo). Sustituye el badge de versión fija que estaba hardcodeada (W5.4).
 */

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight, User, LogIn, LogOut, Sliders, ChevronDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "@/components/auth/AuthModal";
import { useEngineVersion } from "@/hooks/useEngineVersion";

interface BreadcrumbMap {
  [key: string]: { section: string; title: string };
}

/** Solo las rutas de la misión (8 del Sidebar + Ultra + cuenta). Sin rutas en cuarentena. */
const ROUTE_METADATA: BreadcrumbMap = {
  "/": { section: "Inicio", title: "Centro de Mando" },
  "/estrategias": { section: "Estrategias", title: "Catálogo Canónico de Estrategias" },
  "/candidatos": { section: "Candidatos", title: "Candidatos SQLite WAL" },
  "/gates": { section: "Gates", title: "Pipeline de 11 Evidence Gates" },
  "/fondeo": { section: "Fondeo", title: "Trading Desk FONDEO (CME Futures)" },
  "/prop-firms": { section: "Prop-firms", title: "Catálogo de Prop Firms CME" },
  "/plan": { section: "Plan", title: "Plan Maestro & Estado del Proyecto" },
  "/sistema": { section: "Sistema", title: "Telemetría & Supervisor 24/7" },
  "/ultra": { section: "Ultra", title: "Trading Desk ULTRA — EN CONSTRUCCIÓN" },
  "/perfil": { section: "Cuenta", title: "Perfil & Conexiones Broker" },
  "/login": { section: "Cuenta", title: "Acceso a la Plataforma" },
  "/registro": { section: "Cuenta", title: "Registro de Usuario" },
};

export default function Header() {
  const pathname = usePathname() || "/";
  const { user, profile, loading, logout } = useAuth();
  const { version: engineVersion, error: engineError } = useEngineVersion();

  const [timeUtc, setTimeUtc] = useState<string>("");
  const [mounted, setMounted] = useState<boolean>(false);

  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("login");

  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const updateClock = () => {
      const now = new Date();
      setTimeUtc(
        now.toLocaleTimeString("en-GB", { timeZone: "UTC", hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }) +
          " UTC"
      );
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const meta = ROUTE_METADATA[pathname] || {
    section: "Plataforma",
    title: pathname.replace(/^\//, "").replace(/-/g, " ").toUpperCase() || "General",
  };

  const displayName = profile?.displayName || user?.displayName || user?.email?.split("@")[0] || "Trader";
  const userInitial = displayName.charAt(0).toUpperCase();

  const handleOpenAuth = (tab: "login" | "register") => {
    setAuthModalTab(tab);
    setIsAuthModalOpen(true);
  };

  const apiConnected = !engineError && Boolean(engineVersion);

  return (
    <>
      <header
        suppressHydrationWarning
        className="h-11 sticky top-0 z-[100] px-3.5 sm:px-5 flex items-center justify-between gap-3 select-none"
        style={{ background: "var(--bg)", borderBottom: "1px solid var(--border)", color: "var(--text-1)" }}
      >
        {/* BREADCRUMBS */}
        <div className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs font-mono min-w-0 overflow-hidden">
          <Link href="/" style={{ color: "var(--text-2)" }} className="font-bold shrink-0 tracking-wider hover:opacity-80">
            ULTRARENTABLE
          </Link>
          <ChevronRight className="w-3 h-3 shrink-0" style={{ color: "var(--text-3)" }} />
          <span style={{ color: "var(--text-2)" }} className="font-medium truncate hidden xs:inline">
            {meta.section}
          </span>
          <ChevronRight className="w-3 h-3 shrink-0 hidden xs:inline" style={{ color: "var(--text-3)" }} />
          <span style={{ color: "var(--text-1)" }} className="font-bold tracking-tight truncate">
            {meta.title}
          </span>
        </div>

        {/* ESTADO DEL MOTOR, CONEXIÓN API, RELOJ & AUTH */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0 font-mono">
          {/* Versión REAL del motor + punto de conexión API (docs/19 §3) */}
          <div
            className="flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10.5px] font-bold tracking-wide"
            style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: apiConnected ? "var(--text-1)" : "var(--text-3)" }}
            title={engineError ? `API no disponible: ${engineError}` : `Motor ${engineVersion}`}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: apiConnected ? "var(--profit)" : "var(--text-3)" }}
            />
            <span className="hidden sm:inline">{engineVersion ? `MOTOR ${engineVersion}` : "MOTOR: NO DISPONIBLE"}</span>
            <span className="sm:hidden">{engineVersion ? engineVersion : "N/D"}</span>
          </div>

          {/* Reloj UTC */}
          {mounted && (
            <div className="hidden md:flex items-center text-[11px] font-mono tabular-nums" style={{ color: "var(--text-2)" }}>
              {timeUtc}
            </div>
          )}

          {/* AUTENTICACIÓN FIREBASE */}
          {loading ? (
            <div className="h-7 w-20 rounded-md animate-pulse" style={{ background: "var(--surface-1)", border: "1px solid var(--border)" }} />
          ) : user ? (
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 px-2 py-1 rounded-lg text-xs transition-colors"
                style={{ background: "var(--surface-1)", border: "1px solid var(--border)", color: "var(--text-1)" }}
              >
                {user.photoURL ? (
                  <img src={user.photoURL} alt={displayName} className="w-5 h-5 rounded-full object-cover" style={{ border: "1px solid var(--border-strong)" }} />
                ) : (
                  <div
                    className="w-5 h-5 rounded-full font-bold text-[10px] flex items-center justify-center"
                    style={{ background: "var(--surface-3)", color: "var(--text-1)" }}
                  >
                    {userInitial}
                  </div>
                )}
                <span className="font-medium max-w-[100px] truncate hidden sm:inline" style={{ color: "var(--text-1)" }}>
                  {displayName}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isDropdownOpen ? "rotate-180" : ""}`} style={{ color: "var(--text-3)" }} />
              </button>

              {isDropdownOpen && (
                <div
                  className="absolute right-0 mt-1.5 w-64 rounded-xl shadow-2xl py-1.5 z-[150]"
                  style={{ background: "var(--bg)", border: "1px solid var(--border-strong)" }}
                >
                  <div className="px-3.5 py-2.5" style={{ borderBottom: "1px solid var(--border)" }}>
                    <p className="text-xs font-bold truncate" style={{ color: "var(--text-1)" }}>{displayName}</p>
                    <p className="text-[10.5px] font-mono truncate" style={{ color: "var(--text-3)" }}>{user.email}</p>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span
                        className="px-1.5 py-0.5 rounded text-[9.5px] font-mono font-semibold uppercase"
                        style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--text-2)" }}
                      >
                        {profile?.is_superadmin ? "SUPER ADMIN" : (profile?.role || "TRADER")}
                      </span>
                    </div>
                  </div>

                  <div className="py-1">
                    <Link
                      href="/perfil"
                      onClick={() => setIsDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-xs transition-colors"
                      style={{ color: "var(--text-2)" }}
                    >
                      <User className="w-3.5 h-3.5" style={{ color: "var(--text-3)" }} />
                      <span>Mi Perfil & Brokers</span>
                    </Link>
                    <Link
                      href="/fondeo"
                      onClick={() => setIsDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-xs transition-colors"
                      style={{ color: "var(--text-2)" }}
                    >
                      <Sliders className="w-3.5 h-3.5" style={{ color: "var(--text-3)" }} />
                      <span>Mesa Fondeo & Conexión</span>
                    </Link>
                  </div>

                  <div className="pt-1" style={{ borderTop: "1px solid var(--border)" }}>
                    <button
                      type="button"
                      onClick={async () => {
                        setIsDropdownOpen(false);
                        await logout();
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-left transition-colors"
                      style={{ color: "var(--loss)" }}
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => handleOpenAuth("login")}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold tracking-wide transition-all"
              style={{ background: "var(--surface-2)", border: "1px solid var(--border-strong)", color: "var(--text-1)" }}
            >
              <LogIn className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Acceder / Registro</span>
              <span className="sm:hidden">Acceder</span>
            </button>
          )}
        </div>
      </header>

      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} initialTab={authModalTab} />
    </>
  );
}
