"use client";

/**
 * apps/web/components/layout/AppShell.tsx
 * Reescrito 2026-09-01 (AG-11, T5 del contrato de poda web) conforme a
 * docs/19_UI_STYLE_SPEC.md: monocromo sobre --bg, sin azules/ámbar/morados/gradientes de
 * marketing. El único color es --profit (verde, "operativo"/"autorizado") y --loss (rojo,
 * solo para el estado de error/cierre de sesión). El contenido y la estructura no cambian,
 * solo la piel visual — el paso 2 (contenido de /estrategias) no toca este fichero.
 */

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
  ArrowRight,
  RefreshCw,
  LogOut,
  Clock,
} from "lucide-react";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, profile, loading, isAuthorized, logout, refreshProfile } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState<"login" | "register">("register");
  const [refreshing, setRefreshing] = useState(false);

  const openAuth = (tab: "login" | "register") => {
    setAuthModalTab(tab);
    setAuthModalOpen(true);
  };

  const handleRefreshCheck = async () => {
    setRefreshing(true);
    try {
      await refreshProfile();
    } finally {
      setTimeout(() => setRefreshing(false), 500);
    }
  };

  // 1. ESTADO DE CARGA GLOBAL
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen w-full bg-[var(--bg)] text-[var(--text-1)] font-sans p-4">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl flex items-center justify-center bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-2)]">
            <Zap className="w-6 h-6" />
          </div>
          <div className="text-center space-y-1">
            <span className="text-sm font-bold font-mono tracking-wider text-[var(--text-1)]">ULTRARENTABLE</span>
            <p className="text-xs font-mono text-[var(--text-3)]">Verificando autorización y credenciales…</p>
          </div>
        </div>
      </div>
    );
  }

  // 2. VISTA PÚBLICA: USUARIOS NO AUTENTICADOS
  if (!user) {
    return (
      <div className="min-h-screen w-full bg-[var(--bg)] text-[var(--text-1)] font-sans flex flex-col justify-between p-4 sm:p-8 md:p-12 overflow-x-hidden">
        <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} initialTab={authModalTab} />

        <header className="max-w-6xl w-full mx-auto flex items-center justify-between py-4 border-b border-[var(--border)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center font-black text-lg bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-1)]">
              UR
            </div>
            <div>
              <span className="text-sm font-black tracking-tight block text-[var(--text-1)]">ULTRARENTABLE</span>
              <span className="text-[10px] font-mono font-bold block text-[var(--text-3)]">QUANT LAB</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => openAuth("login")}
              className="px-4 py-2 rounded-xl text-xs font-bold transition active:scale-95 cursor-pointer flex items-center gap-1.5 bg-[var(--surface-1)] hover:bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] hover:text-[var(--text-1)]"
            >
              <Key className="w-3.5 h-3.5" />
              <span>Iniciar Sesión</span>
            </button>
            <button
              onClick={() => openAuth("register")}
              className="px-4 py-2 rounded-xl text-xs font-black transition active:scale-95 cursor-pointer flex items-center gap-1.5 bg-[var(--surface-3)] hover:opacity-90 border border-[var(--border-strong)] text-[var(--text-1)]"
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Crear Cuenta</span>
            </button>
          </div>
        </header>

        <main className="max-w-5xl w-full mx-auto space-y-12 py-10 sm:py-16 text-center">
          <section className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-bold tracking-wider uppercase bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-2)]">
              <span>Acceso Exclusivo · Gobernanza Super Admin</span>
            </div>

            <h1 className="text-3xl sm:text-5xl md:text-6xl font-black tracking-tight leading-tight sm:leading-tight text-[var(--text-1)]">
              Plataforma Cuantitativa y Minería de Estrategias con Evidencia Real
            </h1>

            <p className="text-sm sm:text-base max-w-2xl mx-auto leading-relaxed text-[var(--text-2)]">
              Descubrimiento algorítmico, auditoría en 11 Evidence Gates y meta-portafolios de paridad de riesgo.
              Para acceder al panel operativo es obligatorio autenticarte. Los nuevos registros son revisados y autorizados por el Super Administrador.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
              <button
                onClick={() => openAuth("register")}
                className="px-7 py-4 rounded-2xl font-black text-sm tracking-wide transition hover:scale-105 active:scale-95 cursor-pointer flex items-center gap-2.5 bg-[var(--surface-3)] hover:opacity-90 border border-[var(--border-strong)] text-[var(--text-1)]"
              >
                <Zap className="w-4 h-4" />
                <span>Registrarse con Google / Email</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={() => openAuth("login")}
                className="px-7 py-4 rounded-2xl font-bold text-sm transition active:scale-95 cursor-pointer flex items-center gap-2 bg-[var(--surface-1)] hover:bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]"
              >
                <Key className="w-4 h-4" />
                <span>Acceder a mi Cuenta</span>
              </button>
            </div>
          </section>

          {/* 3 PILARES — monocromo, sin acentos de color por pilar */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left">
            <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 space-y-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--surface-2)] text-[var(--text-2)]">
                <Building2 className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider block text-[var(--text-3)]">
                Pilar 01 · Institucional
              </span>
              <h3 className="text-base font-black text-[var(--text-1)]">Track FONDEO (CME & FX)</h3>
              <p className="text-xs leading-relaxed text-[var(--text-2)]">
                Algoritmos optimizados para superar evaluaciones de Prop Firms. Control de Drawdown (DD ≤ 4.0%), Daily Loss Limit y cierre diario obligatorio.
              </p>
            </div>

            <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 space-y-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--surface-2)] text-[var(--text-2)]">
                <Flame className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider block text-[var(--text-3)]">
                Pilar 02 · Convexidad
              </span>
              <h3 className="text-base font-black text-[var(--text-1)]">Track ULTRA (Perpetuos)</h3>
              <p className="text-xs leading-relaxed text-[var(--text-2)]">
                Asimetría convexa Taleb en margen aislado ($100–$1,000) con piramidación autofinanciada por beneficios flotantes.
              </p>
            </div>

            <div className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-6 space-y-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--surface-2)] text-[var(--text-2)]">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider block text-[var(--text-3)]">
                Pilar 03 · Cero Sobreajuste
              </span>
              <h3 className="text-base font-black text-[var(--text-1)]">11 Evidence Gates</h3>
              <p className="text-xs leading-relaxed text-[var(--text-2)]">
                Auditoría en holdout fuera de muestra (OOS), Monte Carlo (0% ruina), estrés 3x slippage y reconciliación tick-a-tick.
              </p>
            </div>
          </section>

          <section className="bg-[var(--surface-1)] border border-[var(--border)] rounded-2xl p-5 flex flex-wrap items-center justify-center gap-6 text-xs font-mono text-[var(--text-2)]">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" style={{ color: "var(--profit)" }} />
              <span>Doctrina Zero-Mocks (100% Real-Only)</span>
            </div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 shrink-0 text-[var(--text-3)]" />
              <span>SQLite WAL + Firebase Cloud</span>
            </div>
          </section>
        </main>

        <footer className="max-w-6xl w-full mx-auto py-6 border-t border-[var(--border)] text-center text-xs font-mono text-[var(--text-3)]">
          UltraRentable Quant Lab © 2026 · Todos los derechos reservados
        </footer>
      </div>
    );
  }

  // 3. VISTA DE BLOQUEO: USUARIO REGISTRADO PERO NO AUTORIZADO
  if (!isAuthorized) {
    return (
      <div className="min-h-screen w-full bg-[var(--bg)] text-[var(--text-1)] font-sans flex flex-col items-center justify-center p-4 sm:p-6">
        <div className="w-full max-w-lg rounded-3xl p-8 text-center space-y-6 bg-[var(--surface-1)] border border-[var(--border-strong)]">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
            <Clock className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]">
              <span>Acceso en Espera de Autorización</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-[var(--text-1)]">Cuenta Registrada en Firebase</h1>
            <p className="text-xs font-mono text-[var(--text-2)]">
              Usuario: <span className="font-semibold text-[var(--text-1)]">{user.email}</span>
            </p>
          </div>

          <div className="p-4 rounded-2xl text-xs leading-relaxed text-left space-y-2 font-sans bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-2)]">
            <p>
              Por directiva de gobernanza y seguridad de <strong className="text-[var(--text-1)] font-mono">UltraRentable Quant Lab</strong>, el acceso a los motores algorítmicos, datos SQLite WAL y trading desk está restringido.
            </p>
            <p className="text-[var(--text-2)]">
              El Super Administrador (<strong className="text-[var(--text-1)] font-mono">josferestudio@gmail.com</strong>) debe autorizar tu perfil desde su panel de control para habilitar tu acceso.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={handleRefreshCheck}
              disabled={refreshing}
              className="w-full py-3 px-4 text-xs font-bold rounded-xl transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 bg-[var(--surface-3)] hover:opacity-90 border border-[var(--border-strong)] text-[var(--text-1)]"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              <span>{refreshing ? "Comprobando autorización…" : "Comprobar si ya he sido autorizado"}</span>
            </button>

            <button
              onClick={() => logout()}
              className="w-full py-2.5 px-4 text-xs font-semibold rounded-xl transition flex items-center justify-center gap-2 cursor-pointer bg-[var(--surface-1)] hover:bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)]"
            >
              <LogOut className="w-3.5 h-3.5" style={{ color: "var(--loss)" }} />
              <span>Cerrar Sesión / Entrar con otra cuenta</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 4. VISTA COMPLETA: USUARIO AUTORIZADO (SIDEBAR + HEADER + PLATAFORMA ACTIVA)
  return (
    <div className="flex min-h-screen w-full bg-[var(--bg)] text-[var(--text-1)] overflow-x-hidden">
      <React.Suspense fallback={<aside className="w-[220px] min-w-[220px] max-w-[220px] h-screen bg-[var(--bg)] border-r border-[var(--border)] sticky top-0 z-[110]" />}>
        <Sidebar />
      </React.Suspense>
      <div className="flex flex-col flex-1 min-w-0 min-h-screen overflow-x-hidden bg-[var(--bg)]">
        <Header />
        <main className="flex-1 p-3.5 sm:p-5 md:p-6 lg:p-7 overflow-y-auto overflow-x-hidden max-w-full">{children}</main>
      </div>
    </div>
  );
}
