"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import AuthModal from "@/components/auth/AuthModal";
import {
  Zap,
  Building2,
  Flame,
  ShieldCheck,
  CheckCircle2,
  Database,
  Key,
  Sparkles,
  Lock,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("register");

  const openAuth = (tab: "login" | "register") => {
    setAuthModalTab(tab);
    setAuthModalOpen(true);
  };

  // 1. ESTADO DE CARGA GLOBAL
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen w-full bg-[#030712] text-slate-100 font-sans p-4">
        <div className="flex flex-col items-center gap-4 animate-in fade-in duration-300">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Zap className="w-6 h-6 animate-pulse" />
          </div>
          <div className="text-center space-y-1">
            <span className="text-sm font-bold font-mono tracking-wider text-slate-200">ULTRARENTABLE QUANT LAB</span>
            <p className="text-xs text-slate-500 font-mono">Verificando sesión segura...</p>
          </div>
        </div>
      </div>
    );
  }

  // 2. VISTA EXCLUSIVA: LANDING ÚNICO PARA USUARIOS NO AUTENTICADOS (SIN SIDEBAR, SIN HEADER INTERNO)
  if (!user) {
    return (
      <div className="min-h-screen w-full bg-[#030712] text-slate-100 font-sans flex flex-col justify-between p-4 sm:p-8 md:p-12 overflow-x-hidden selection:bg-emerald-500/20 selection:text-emerald-300">
        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          initialTab={authModalTab}
        />

        {/* CABECERA MINIMALISTA PÚBLICA */}
        <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-600 flex items-center justify-center text-slate-950 font-black text-lg shadow-md shadow-emerald-950/50">
              ⚡
            </div>
            <div>
              <span className="text-sm font-black tracking-tight text-white block">ULTRARENTABLE</span>
              <span className="text-[10px] font-mono text-emerald-400 font-bold block">QUANT LAB v5.4.0</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => openAuth("login")}
              className="px-4 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white bg-slate-900/80 hover:bg-slate-800 border border-slate-800 transition active:scale-95 cursor-pointer flex items-center gap-1.5"
            >
              <Key className="w-3.5 h-3.5 text-sky-400" />
              <span>Iniciar Sesión</span>
            </button>
            <button
              onClick={() => openAuth("register")}
              className="px-4 py-2 rounded-xl text-xs font-black text-slate-950 bg-emerald-500 hover:bg-emerald-400 transition shadow-md shadow-emerald-900/30 active:scale-95 cursor-pointer flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5 fill-current" />
              <span>Crear Cuenta</span>
            </button>
          </div>
        </header>

        {/* CUERPO DEL LANDING */}
        <main className="max-w-5xl w-full mx-auto space-y-12 py-10 sm:py-16 text-center">
          {/* HERO */}
          <section className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs font-mono font-bold tracking-wider uppercase shadow-inner">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Acceso Restringido · Requiere Registro de Usuario</span>
            </div>

            <h1 className="text-3xl sm:text-5xl md:text-6xl font-black text-white tracking-tight leading-tight sm:leading-tight">
              Plataforma Cuantitativa y Minería de Estrategias con{" "}
              <span className="bg-gradient-to-r from-emerald-400 via-sky-400 to-indigo-400 bg-clip-text text-transparent">
                Evidencia Real
              </span>
            </h1>

            <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto leading-relaxed">
              Descubrimiento algorítmico, auditoría en 11 Evidence Gates y meta-portafolios de paridad de riesgo.
              Para acceder al panel operativo, minería y herramientas de trading es obligatorio autenticarte con tu cuenta de usuario.
            </p>

            {/* BOTONES PRINCIPALES DE ACCIÓN */}
            <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
              <button
                onClick={() => openAuth("register")}
                className="px-7 py-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-sm tracking-wide shadow-xl shadow-emerald-900/40 transition hover:scale-105 active:scale-95 cursor-pointer flex items-center gap-2.5"
              >
                <Zap className="w-4 h-4 fill-current" />
                <span>Registrarse Gratis con Google / Email</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => openAuth("login")}
                className="px-7 py-4 rounded-2xl bg-[#090d16] hover:bg-slate-900 border border-slate-700 text-slate-200 font-bold text-sm transition active:scale-95 cursor-pointer flex items-center gap-2 shadow-sm"
              >
                <Key className="w-4 h-4 text-sky-400" />
                <span>Acceder a mi Cuenta</span>
              </button>
            </div>
          </section>

          {/* 3 PILARES EXPLICATIVOS */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left">
            <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-3 shadow-xl">
              <div className="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center font-bold">
                <Building2 className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold text-sky-400 uppercase tracking-wider block">
                Pilar 01 · Institucional
              </span>
              <h3 className="text-base font-black text-white">Track FONDEO (CME & FX)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Algoritmos optimizados para superar evaluaciones de Prop Firms. Control estricto de Drawdown ($DD \le 4.0\%$), Daily Loss Limit y cierre diario obligatorio.
              </p>
            </div>

            <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-3 shadow-xl">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold">
                <Flame className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-wider block">
                Pilar 02 · Convexidad
              </span>
              <h3 className="text-base font-black text-white">Track ULTRA (Perpetuos)</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Asimetría convexa Taleb en margen aislado ($100–$1,000) con piramidación autofinanciada por beneficios flotantes y cosecha a Bóveda Ratchet.
              </p>
            </div>

            <div className="bg-[#090d16]/90 backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 space-y-3 shadow-xl">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase tracking-wider block">
                Pilar 03 · Cero Sobreajuste
              </span>
              <h3 className="text-base font-black text-white">11 Evidence Gates</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Auditoría en holdout ciego fuera de muestra (OOS), remuestreo Monte Carlo (0% ruina), estrés 3x slippage y reconciliación tick-a-tick con NautilusTrader.
              </p>
            </div>
          </section>

          {/* DOCTRINA ZERO-MOCKS */}
          <section className="bg-[#090d16]/60 border border-white/[0.06] rounded-2xl p-5 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400 font-mono">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Doctrina Zero-Mocks (100% Real-Only)</span>
            </div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>Base de Datos SQLite WAL + Firebase Auth</span>
            </div>
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Sellado Criptográfico SHA-256</span>
            </div>
          </section>
        </main>

        {/* PIE DE PÁGINA PÚBLICO */}
        <footer className="max-w-6xl w-full mx-auto py-6 border-t border-white/[0.06] text-center text-xs text-slate-500 font-mono">
          UltraRentable Quant Lab © 2026 · Todos los derechos reservados · Plataforma Cuantitativa Protegida
        </footer>
      </div>
    );
  }

  // 3. VISTA COMPLETA: USUARIO REGISTRADO Y AUTENTICADO (SIDEBAR + HEADER + PLATAFORMA ACTIVA)
  return (
    <div className="flex min-h-screen w-full bg-[#030712] text-slate-100 overflow-x-hidden">
      <React.Suspense
        fallback={
          <aside className="w-[250px] min-w-[250px] max-w-[250px] h-screen bg-[#070a10] border-r border-white/[0.07] sticky top-0 z-[110]" />
        }
      >
        <Sidebar />
      </React.Suspense>
      <div className="flex flex-col flex-1 min-w-0 min-h-screen overflow-x-hidden bg-[#030712]">
        <Header />
        <main className="flex-1 p-3.5 sm:p-5 md:p-6 lg:p-7 overflow-y-auto overflow-x-hidden max-w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
