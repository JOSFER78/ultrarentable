"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShieldCheck,
  Mail,
  Lock,
  User,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function RegistroPage() {
  const router = useRouter();
  const { user, register, loginWithGoogle, loading: authLoading } = useAuth();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

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
      case "auth/email-already-in-use":
        return "Ya existe una cuenta con este correo electrónico.";
      case "auth/weak-password":
        return "La contraseña debe tener al menos 6 caracteres.";
      case "auth/invalid-email":
        return "El formato de correo electrónico no es válido.";
      case "auth/popup-closed-by-user":
        return "Inicio de sesión con Google cancelado.";
      default:
        return err?.message || "Ocurrió un error al registrar la cuenta.";
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!displayName.trim() || !email.trim() || !password.trim()) {
      setErrorMessage("Por favor, completa todos los campos.");
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage("Las contraseñas no coinciden.");
      return;
    }

    if (password.length < 6) {
      setErrorMessage("La contraseña debe tener al menos 6 caracteres.");
      return;
    }

    setLoading(true);
    try {
      await register(email.trim(), password, displayName.trim());
      setSuccessMessage("¡Cuenta creada y sincronizada en Firestore! Redirigiendo...");
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
        <div className="max-w-md w-full bg-[var(--surface-1)] border border-white/[0.1] rounded-2xl p-8 backdrop-blur-xl shadow-2xl">
          <div className="w-12 h-12 rounded-xl bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] flex items-center justify-center mx-auto mb-4">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-[var(--text-1)] mb-2">Cuenta Activa</h2>
          <p className="text-xs text-[var(--text-2)] mb-6 font-mono">
            Conectado como <span className="text-[var(--profit)] font-semibold">{user.email}</span>
          </p>
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-1)] text-xs font-bold rounded-xl transition-all shadow-lg "
          >
            <span>Ir al Centro de Mando</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[75vh] p-4 font-sans">
      <div className="w-full max-w-md bg-[var(--bg)] border border-[var(--border-strong)] rounded-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 pb-4 border-b border-[var(--border)] text-center">
          <div className="w-9 h-9 rounded-md bg-[var(--surface-2)] border border-[var(--border)] text-[var(--profit)] flex items-center justify-center mx-auto mb-2.5">
            <Sparkles className="w-4 h-4" />
          </div>
          <h1 className="text-base font-bold text-[var(--text-1)] tracking-tight">
            Registro en UltraRentable
          </h1>
          <p className="text-[11px] text-[var(--text-2)] font-mono mt-0.5">
            Perfil de usuario sincronizado en Firestore
          </p>
        </div>

        {/* Form */}
        <div className="p-5 space-y-3.5">
          {errorMessage && (
            <div className="p-2.5 rounded-md bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)] text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[var(--loss)]" />
              <div className="flex-1 font-medium">{errorMessage}</div>
            </div>
          )}

          {successMessage && (
            <div className="p-2.5 rounded-md bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-xs flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[var(--profit)]" />
              <div className="flex-1 font-medium">{successMessage}</div>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                Nombre Completo o Alias
              </label>
              <div className="relative">
                <User className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                <input
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Trader Master Quant"
                  className="w-full pl-9 pr-3 py-2 bg-[var(--surface-1)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded-md text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                Correo Electrónico
              </label>
              <div className="relative">
                <Mail className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="trader@quant.com"
                  className="w-full pl-9 pr-3 py-2 bg-[var(--surface-1)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded-md text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                  Contraseña
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Mín. 6 chars"
                    className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded-md text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all font-mono"
                  />
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                  Confirmar
                </label>
                <div className="relative">
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repetir clave"
                    className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded-md text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all font-mono"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || googleLoading}
              className="w-full mt-2 py-2.5 px-4 bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-1)] text-xs font-semibold rounded-md disabled:opacity-50 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sincronizando con Firestore...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Registrar Cuenta</span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-[var(--border)]"></div>
            <span className="flex-shrink mx-3 text-[10px] uppercase font-mono tracking-widest text-[var(--text-3)]">
              o
            </span>
            <div className="flex-grow border-t border-[var(--border)]"></div>
          </div>

          {/* Google Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading || googleLoading}
            className="w-full py-2.5 px-4 bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-[var(--text-1)] text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 cursor-pointer"
          >
            {googleLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-[var(--profit)]" />
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

          {/* Switch to Login */}
          <div className="pt-2 text-center text-xs text-[var(--text-2)] font-mono">
            ¿Ya tienes una cuenta registrada?{" "}
            <Link
              href="/login"
              className="text-[var(--profit)] hover:text-[var(--profit)] font-bold underline underline-offset-4"
            >
              Inicia sesión aquí
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
