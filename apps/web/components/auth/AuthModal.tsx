"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import {
  X,
  Mail,
  Lock,
  User,
  ShieldCheck,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  CheckCircle2,
  Sparkles,
  Crown,
} from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialTab?: "login" | "register";
}

export default function AuthModal({
  isOpen,
  onClose,
  initialTab = "login",
}: AuthModalProps) {
  const { login, register, loginWithGoogle, user } = useAuth();
  const [activeTab, setActiveTab] = useState<"login" | "register">(initialTab);

  // Form states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Status states
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    setActiveTab(initialTab);
    setErrorMessage(null);
    setSuccessMessage(null);
  }, [initialTab, isOpen]);

  // Close when user becomes authenticated
  useEffect(() => {
    if (user && isOpen) {
      const timer = setTimeout(() => {
        onClose();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [user, isOpen, onClose]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const parseFirebaseError = (err: any): string => {
    const code = err?.code || "";
    switch (code) {
      case "auth/invalid-credential":
      case "auth/wrong-password":
      case "auth/user-not-found":
        return "Credenciales inválidas. Comprueba tu correo y contraseña.";
      case "auth/email-already-in-use":
        return "Ya existe una cuenta con este correo electrónico.";
      case "auth/weak-password":
        return "La contraseña es muy débil. Debe tener al menos 6 caracteres.";
      case "auth/configuration-not-found":
        return "Firebase Auth no está activado en el proyecto 'pecemi'. Ve a Firebase Console > Authentication > Get started y activa el proveedor Google.";
      case "auth/unauthorized-domain":
        return "Dominio no autorizado en Firebase. Añade 'localhost' en Firebase Console > Authentication > Settings > Authorized domains.";
      case "auth/popup-blocked":
        return "El navegador bloqueó la ventana emergente de Google. Habilita los popups en la barra de direcciones de tu navegador.";
      default:
        if (err?.message?.includes("CONFIGURATION_NOT_FOUND") || err?.message?.includes("configuration-not-found")) {
          return "Firebase Auth no está activado en el proyecto 'pecemi'. Ve a Firebase Console > Authentication > Get started y activa Google.";
        }
        return err?.message || "Ocurrió un error en la autenticación.";
    }
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!email.trim() || !password.trim()) {
      setErrorMessage("Por favor, completa todos los campos requeridos.");
      return;
    }

    setLoading(true);
    try {
      await login(email.trim(), password);
      setSuccessMessage("¡Sesión iniciada con éxito!");
    } catch (err: any) {
      setErrorMessage(parseFirebaseError(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!email.trim() || !password.trim() || !displayName.trim()) {
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
      setSuccessMessage("¡Cuenta creada y sincronizada en Firestore!");
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
      setSuccessMessage("¡Conectado exitosamente con Google!");
    } catch (err: any) {
      setErrorMessage(parseFirebaseError(err));
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-md bg-[var(--bg)] border border-[var(--border-strong)] rounded-lg shadow-2xl overflow-hidden z-10 animate-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="px-6 pt-5 pb-4 flex items-center justify-between border-b border-[var(--border)]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--text-2)]">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[var(--text-1)] tracking-tight flex items-center gap-1.5">
                UltraRentable <span className="text-[var(--text-2)] font-mono text-xs">Auth</span>
              </h3>
              <p className="text-[11px] text-[var(--text-2)] font-mono">
                Pecemi Quant Hub & Gateway
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--text-2)] hover:text-[var(--text-1)] hover:bg-white/[0.08] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selector */}
        <div className="px-6 pt-4">
          <div className="grid grid-cols-2 p-1 bg-[var(--surface-1)] border border-white/[0.06] rounded-xl text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setActiveTab("login");
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2 px-3 rounded-lg transition-all ${
                activeTab === "login"
                  ? "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)] shadow-sm"
                  : "text-[var(--text-2)] hover:text-[var(--text-1)]"
              }`}
            >
              Iniciar Sesión
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveTab("register");
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className={`py-2 px-3 rounded-lg transition-all ${
                activeTab === "register"
                  ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)] shadow-sm"
                  : "text-[var(--text-2)] hover:text-[var(--text-1)]"
              }`}
            >
              Crear Cuenta
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 pt-4 space-y-4">
          {/* Alerts */}
          {errorMessage && (
            <div className="p-3 rounded-xl bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)] text-xs flex items-start gap-2 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[var(--loss)]" />
              <div className="flex-1 font-medium leading-relaxed">{errorMessage}</div>
            </div>
          )}

          {successMessage && (
            <div className="p-3 rounded-xl bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-xs flex items-start gap-2 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[var(--profit)]" />
              <div className="flex-1 font-medium leading-relaxed">{successMessage}</div>
            </div>
          )}

          {/* Login Form */}
          {activeTab === "login" ? (
            <form onSubmit={handleLoginSubmit} className="space-y-3.5">
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1.5 font-mono">
                  Correo Electrónico
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="trader@quant.com"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--border)] focus:ring-1 focus:ring-[var(--border-strong)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1.5 font-mono">
                  Contraseña
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-10 pr-10 py-2.5 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--border)] focus:ring-1 focus:ring-[var(--border-strong)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[var(--text-3)] hover:text-[var(--text-1)]"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
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
                    <span>Verificando acceso...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Acceder a la Plataforma</span>
                  </>
                )}
              </button>
            </form>
          ) : (
            /* Register Form */
            <form onSubmit={handleRegisterSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                  Nombre Completo o Alias
                </label>
                <div className="relative">
                  <User className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                  <input
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Trader Master Quant"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] focus:ring-1 focus:ring-[var(--border-strong)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                  Correo Electrónico
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-3)]" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="trader@quant.com"
                    className="w-full pl-10 pr-3.5 py-2.5 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] focus:ring-1 focus:ring-[var(--border-strong)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all"
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
                      type={showPassword ? "text" : "password"}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Mín. 6 chars"
                      className="w-full px-3 py-2.5 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] focus:ring-1 focus:ring-[var(--border-strong)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-[var(--text-1)] mb-1 font-mono">
                    Confirmar
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repetir clave"
                      className="w-full px-3 py-2.5 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] focus:ring-1 focus:ring-[var(--border-strong)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none transition-all font-mono"
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
                    <span>Creando perfil en Firestore...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Crear Cuenta & Sincronizar</span>
                  </>
                )}
              </button>
            </form>
          )}

          {/* Social Sign-in Divider */}
          <div className="relative flex py-1 items-center">
            <div className="flex-grow border-t border-white/[0.08]"></div>
            <span className="flex-shrink mx-3 text-[10px] uppercase font-mono tracking-widest text-[var(--text-3)]">
              o continuar con
            </span>
            <div className="flex-grow border-t border-white/[0.08]"></div>
          </div>

          {/* Google Sign In Button */}
          <button
            type="button"
            onClick={handleGoogleSignIn}
            disabled={loading || googleLoading}
            className="w-full py-2.5 px-4 bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-[var(--text-1)] text-xs font-semibold rounded-md transition-all flex items-center justify-center gap-2.5 disabled:opacity-50 cursor-pointer"
          >
            {googleLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-[var(--text-2)]" />
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


        </div>

        {/* Footer info */}
        <div className="px-6 py-3 bg-black/40 border-t border-white/[0.04] text-[10.5px] text-[var(--text-3)] text-center font-mono">
          Autenticación segura Firebase v12 · Zero-Mocks Real-Only
        </div>
      </div>
    </div>
  );
}
