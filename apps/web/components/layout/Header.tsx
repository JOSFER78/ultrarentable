"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronRight,
  ShieldCheck,
  User,
  LogIn,
  LogOut,
  Settings,
  Sliders,
  ChevronDown,
  Layers,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import AuthModal from "@/components/auth/AuthModal";

interface BreadcrumbMap {
  [key: string]: { section: string; title: string };
}

const ROUTE_METADATA: BreadcrumbMap = {
  "/": { section: "Inicio", title: "Centro de Mando Cuantitativo" },
  "/fondeo": { section: "Operación & Trading Desks", title: "Trading Desk FONDEO (CME Futures)" },
  "/ultra": { section: "Operación & Trading Desks", title: "Trading Desk ULTRA (BingX Perps)" },
  "/trading-desk": { section: "Operación & Trading Desks", title: "Mesa de Ejecución DOM" },
  "/trading-desk/posiciones": { section: "Operación & Trading Desks", title: "Posiciones & Brackets" },
  "/trading-desk/estrategias": { section: "Operación & Trading Desks", title: "Estrategias Activas" },
  "/trading-desk/riesgo": { section: "Operación & Trading Desks", title: "Sentinel de Riesgo" },
  "/trading-desk/auditoria": { section: "Operación & Trading Desks", title: "Auditoría Forense WAL" },
  "/trading-desk/configuracion": { section: "Operación & Trading Desks", title: "Conexión Gateway" },
  "/estrategias": { section: "Strategy Lab & Quant", title: "Strategy Lab & Descubrimiento" },
  "/candidatos": { section: "Strategy Lab & Quant", title: "Explorador de Candidatos SQLite WAL" },
  "/gates": { section: "Strategy Lab & Quant", title: "Pipeline de 11 Evidence Gates" },
  "/research": { section: "Strategy Lab & Quant", title: "Panel Investigador & Research Lab" },
  "/portfolio": { section: "Strategy Lab & Quant", title: "Portafolio Studio & Paridad de Riesgo" },
  "/prop-firms": { section: "Ecosistema & Información", title: "Catálogo 70 Prop Firms CME" },
  "/tradesfera": { section: "Ecosistema & Información", title: "Dossier Tradesfera (18 Módulos)" },
  "/proveedores": { section: "Ecosistema & Información", title: "Gateways API & MCP Conectores" },
  "/sistema": { section: "Ecosistema & Información", title: "Telemetría & Pulso 24/7" },
  "/perfil": { section: "Cuenta", title: "Perfil & Conexiones Broker" },
  "/login": { section: "Cuenta", title: "Acceso a la Plataforma" },
  "/registro": { section: "Cuenta", title: "Registro de Usuario" },
};

export default function Header() {
  const pathname = usePathname() || "/";
  const { user, profile, loading, logout } = useAuth();

  const [timeUtc, setTimeUtc] = useState<string>("");
  const [timeLocal, setTimeLocal] = useState<string>("");
  const [mounted, setMounted] = useState<boolean>(false);

  // Auth Modal state
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("login");

  // User dropdown menu state
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    const updateClocks = () => {
      const now = new Date();
      setTimeUtc(
        now.toLocaleTimeString("en-GB", {
          timeZone: "UTC",
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }) + " UTC"
      );
      setTimeLocal(
        now.toLocaleTimeString("es-ES", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }) + " LOC"
      );
    };

    updateClocks();
    const interval = setInterval(updateClocks, 1000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
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

  const displayName =
    profile?.displayName ||
    user?.displayName ||
    user?.email?.split("@")[0] ||
    "Trader";

  const userInitial = displayName.charAt(0).toUpperCase();

  const handleOpenAuth = (tab: "login" | "register") => {
    setAuthModalTab(tab);
    setIsAuthModalOpen(true);
  };

  return (
    <>
      <header
        suppressHydrationWarning
        className="h-11 sticky top-0 z-[100] bg-[#080c14]/95 backdrop-blur-xl border-b border-white/[0.07] px-3.5 sm:px-5 flex items-center justify-between gap-3 select-none"
      >
        {/* 1. BREADCRUMBS JERÁRQUICOS */}
        <div className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs font-mono min-w-0 overflow-hidden">
          <Link
            href="/"
            className="text-slate-400 hover:text-slate-200 font-bold transition-colors shrink-0 tracking-wider"
          >
            ULTRARENTABLE
          </Link>
          <ChevronRight className="w-3 h-3 text-slate-600 shrink-0" />
          <span className="text-slate-400 font-medium truncate hidden xs:inline">{meta.section}</span>
          <ChevronRight className="w-3 h-3 text-slate-600 shrink-0 hidden xs:inline" />
          <span className="text-slate-100 font-bold tracking-tight truncate">{meta.title}</span>
        </div>

        {/* 2. ESTADO DEL MOTOR, RELOJES & AUTH */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0 font-mono">
          {/* Badge Real-Only */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 text-[10.5px] font-bold tracking-wide">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.8)] animate-pulse" />
            <span className="hidden sm:inline">v5.4.0 REAL-ONLY</span>
            <span className="sm:hidden">v5.4</span>
          </div>

          {/* Relojes UTC / Local */}
          {mounted && (
            <div className="hidden md:flex items-center gap-2 text-[11px] text-slate-400 font-mono tabular-nums">
              <span className="text-slate-300 font-medium">{timeUtc}</span>
              <span className="text-slate-600">|</span>
              <span className="text-slate-400">{timeLocal}</span>
            </div>
          )}

          {/* 3. SECCIÓN DE AUTENTICACIÓN FIREBASE */}
          {loading ? (
            <div className="h-7 w-20 rounded-md bg-white/[0.04] animate-pulse border border-white/[0.05]" />
          ) : user ? (
            /* USUARIO AUTENTICADO */
            <div className="relative" ref={dropdownRef}>
              <button
                type="button"
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="flex items-center gap-2 px-2 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800/80 border border-white/[0.1] hover:border-sky-500/40 transition-all text-xs text-slate-200"
              >
                {user.photoURL ? (
                  <img
                    src={user.photoURL}
                    alt={displayName}
                    className="w-5 h-5 rounded-full object-cover border border-white/20"
                  />
                ) : (
                  <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-sky-500 to-emerald-500 text-white font-bold text-[10px] flex items-center justify-center shadow-sm">
                    {userInitial}
                  </div>
                )}
                <span className="font-medium text-slate-200 max-w-[100px] truncate hidden sm:inline">
                  {displayName}
                </span>
                <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isDropdownOpen ? "rotate-180" : ""}`} />
              </button>

              {/* DROPDOWN MENU */}
              {isDropdownOpen && (
                <div className="absolute right-0 mt-1.5 w-64 bg-[#080d1a]/95 border border-white/[0.12] rounded-xl shadow-2xl backdrop-blur-2xl py-1.5 z-[150] animate-in fade-in zoom-in-95 duration-150">
                  {/* User Profile Summary */}
                  <div className="px-3.5 py-2.5 border-b border-white/[0.06]">
                    <p className="text-xs font-bold text-white truncate">{displayName}</p>
                    <p className="text-[10.5px] text-slate-400 font-mono truncate">{user.email}</p>
                    <div className="mt-1.5 flex items-center gap-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[9.5px] font-mono font-semibold uppercase ${
                        profile?.is_superadmin
                          ? "bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold"
                          : "bg-sky-500/10 border border-sky-500/30 text-sky-300"
                      }`}>
                        {profile?.is_superadmin ? "SUPER ADMIN" : (profile?.role || "TRADER")}
                      </span>
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[9.5px] font-mono font-semibold">
                        FIRESTORE VERIFIED
                      </span>
                    </div>
                  </div>

                  {/* Navigation Links */}
                  <div className="py-1">
                    <Link
                      href="/perfil"
                      onClick={() => setIsDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:text-white hover:bg-white/[0.06] transition-colors"
                    >
                      <User className="w-3.5 h-3.5 text-sky-400" />
                      <span>Mi Perfil & Brokers</span>
                    </Link>
                    <Link
                      href="/trading-desk/configuracion"
                      onClick={() => setIsDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:text-white hover:bg-white/[0.06] transition-colors"
                    >
                      <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Conexión Gateway & APIs</span>
                    </Link>
                    <Link
                      href="/gates"
                      onClick={() => setIsDropdownOpen(false)}
                      className="flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-300 hover:text-white hover:bg-white/[0.06] transition-colors"
                    >
                      <Layers className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Bóveda Estrategias</span>
                    </Link>
                  </div>

                  {/* Logout Button */}
                  <div className="pt-1 border-t border-white/[0.06]">
                    <button
                      type="button"
                      onClick={async () => {
                        setIsDropdownOpen(false);
                        await logout();
                      }}
                      className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 transition-colors text-left"
                    >
                      <LogOut className="w-3.5 h-3.5 text-rose-400" />
                      <span>Cerrar Sesión</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* USUARIO NO AUTENTICADO */
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => handleOpenAuth("login")}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 text-sky-300 hover:text-white text-xs font-semibold tracking-wide transition-all shadow-sm"
              >
                <LogIn className="w-3.5 h-3.5 text-sky-400" />
                <span className="hidden sm:inline">Acceder / Registro</span>
                <span className="sm:hidden">Acceder</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Auth Modal Global */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        initialTab={authModalTab}
      />
    </>
  );
}
