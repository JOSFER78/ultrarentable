"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  Mail,
  Lock,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ArrowRight,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { user, login, loginWithGoogle, loading: authLoading } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (user && !authLoading) {
      const timer = setTimeout(() => {
        router.push("/");
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [user, authLoading, router]);

  const parseFirebaseError = (err: any): string => {
    const code = err?.code || "";
    switch (code) {
      case "auth/invalid-credential":
      case "auth/wrong-password":
      case "auth/user-not-found":
        return "Credenciales inválidas. Comprueba tu correo y contraseña.";
      case "auth/invalid-email":
        return "El formato de correo electrónico no es válido.";
      case "auth/popup-closed-by-user":
        return "Inicio de sesión con Google cancelado.";
      default:
        return err?.message || "Ocurrió un error al iniciar sesión.";
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!email.trim() || !password.trim()) {
      setErrorMessage("Por favor, introduce tu correo y contraseña.");
      return;
    }

    setLoading(true);
    try {
      await login(email.trim(), password);
      setSuccessMessage("¡Acceso verificado! Redirigiendo al Centro de Mando...");
    } catch (err: any) {
      setErrorMessage(parseFirebaseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setErrorMessage(null);
    setSuccessMessage(null);
    setGoogleLoading(true);
    try {
      await loginWithGoogle();
      setSuccessMessage("¡Conectado con Google! Redirigiendo...");
    } catch (err: any) {
      setErrorMessage(parseFirebaseError(err));
    } finally {
      setGoogleLoading(false);
    }
  };

  if (user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] p-4 text-center">
        <div className="max-w-md w-full bg-[#080d1a]/90 border border-white/[0.1] rounded-2xl p-8 backdrop-blur-xl shadow-2xl">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Sesión Activa</h2>
          <p className="text-xs text-slate-400 mb-6 font-mono">
            Conectado como <span className="text-sky-300 font-semibold">{user.email}</span>
          </p>
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-sky-500/20"
          >
            <span>Ir al Centro de Mando</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[75vh] p-4">
      <div className="w-full max-w-md bg-[#080d1a]/95 border border-white/[0.12] rounded-2xl shadow-[0_0_60px_rgba(0,0,0,0.8)] backdrop-blur-2xl overflow-hidden">
        {/* Glow Accent */}
        <div className="h-1 bg-gradient-to-r from-sky-500 via-emerald-500 to-indigo-500" />

        {/* Header */}
        <div className="p-6 pb-4 border-b border-white/[0.06] text-center">
          <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mx-auto mb-3">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h1 className="text-lg font-bold text-white tracking-tight">
            Acceso UltraRentable Quant Hub
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Autenticación determinista Firebase v12
          </p>
        </div>

        {/* Form */}
        <div className="p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <div className="flex-1 font-medium">{errorMessage}</div>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
              <div className="flex-1 font-medium">{successMessage}</div>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-3.5">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1.5 font-mono">
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="trader@quant.com"
                  className="w-full pl-10 pr-3.5 py-2.5 bg-slate-900/80 border border-white/[0.08] focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1.5 font-mono">
                Contraseña
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-900/80 border border-white/[0.08] focus:border-sky-500/50 focus:ring-1 focus:ring-sky-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none transition-all font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || googleLoading}
              className="w-full mt-2 py-2.5 px-4 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-sky-500/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verificando acceso...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Iniciar Sesión</span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-white/[0.08]"></div>
            <span className="flex-shrink mx-3 text-[10px] uppercase font-mono tracking-widest text-slate-500">
              o
            </span>
            <div className="flex-grow border-t border-white/[0.08]"></div>
          </div>

          {/* Google Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading || googleLoading}
            className="w-full py-2.5 px-4 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.1] hover:border-white/[0.2] text-slate-200 text-xs font-medium rounded-xl transition-all flex items-center justify-center gap-2.5 disabled:opacity-50"
          >
            {googleLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.16 0 9.98 0 12s.45 3.84 1.25 5.42l4.03-3.15z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
                />
              </svg>
            )}
            <span>Continuar con Google</span>
          </button>

          {/* Switch to Register */}
          <div className="pt-2 text-center text-xs text-slate-400 font-mono">
            ¿No tienes cuenta todavía?{" "}
            <Link
              href="/registro"
              className="text-sky-400 hover:text-sky-300 font-bold underline underline-offset-4"
            >
              Regístrate aquí
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
