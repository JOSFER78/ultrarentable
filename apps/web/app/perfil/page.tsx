"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  User,
  ShieldCheck,
  Key,
  Sliders,
  Save,
  CheckCircle2,
  AlertCircle,
  Loader2,
  LogIn,
  Server,
  Layers,
  Sparkles,
  Users,
  UserCheck,
  UserX,
  Crown,
  RefreshCw,
  Bot,
} from "lucide-react";
import { useAuth, UserProfile, isSuperAdminEmail, SUPERADMIN_EMAIL } from "@/context/AuthContext";
import {
  getIAProveedor,
  saveIAProveedor,
  probarIAProveedor,
  type IAProveedorConfig,
  type IAProbarResultado,
} from "@/lib/api";
import AsistenteIA from "@/components/ia/AsistenteIA";
import ConfiguracionMotores from "@/components/superadmin/ConfiguracionMotores";

export default function PerfilPage() {
  const {
    user,
    profile,
    loading: authLoading,
    isSuperAdmin,
    isAuthorized,
    updateUserProfile,
    listAllUsers,
    authorizeUser,
    revokeUser,
  } = useAuth();

  const [displayName, setDisplayName] = useState("");
  const [defaultAsset, setDefaultAsset] = useState("NQ");
  const [notifications, setNotifications] = useState(true);

  // Broker Accounts
  const [tradovateId, setTradovateId] = useState("");
  const [ninjatraderId, setNinjatraderId] = useState("");
  const [pickmytradeToken, setPickmytradeToken] = useState("");
  const [bingxApiKey, setBingxApiKey] = useState("");
  const [bingxSecret, setBingxSecret] = useState("");

  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Super Admin user management state
  const [managedUsers, setManagedUsers] = useState<UserProfile[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [adminActionMsg, setAdminActionMsg] = useState<string | null>(null);

  // Super Admin IA Provider state
  const [iaNombre, setIaNombre] = useState<string>("");
  const [iaEndpoint, setIaEndpoint] = useState<string>("");
  const [iaModelo, setIaModelo] = useState<string>("");
  const [iaApiKey, setIaApiKey] = useState<string>("");
  const [iaTieneClave, setIaTieneClave] = useState<boolean>(false);
  const [iaGuardando, setIaGuardando] = useState<boolean>(false);
  const [iaProbando, setIaProbando] = useState<boolean>(false);
  const [iaPruebaResultado, setIaPruebaResultado] = useState<IAProbarResultado | null>(null);
  const [iaMensaje, setIaMensaje] = useState<string | null>(null);

  const cargarConfigIA = React.useCallback(async () => {
    try {
      const data = await getIAProveedor();
      if (data) {
        setIaNombre(data.nombre || "");
        setIaEndpoint(data.endpoint || "");
        setIaModelo(data.modelo || "");
        setIaTieneClave(data.tiene_clave);
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.displayName || user?.displayName || "");
      setDefaultAsset(profile.preferences?.default_asset || "NQ");
      setNotifications(profile.preferences?.notifications ?? true);
      setTradovateId(profile.broker_accounts?.tradovate_account_id || "");
      setNinjatraderId(profile.broker_accounts?.ninjatrader_account_id || "");
      setPickmytradeToken(profile.broker_accounts?.pickmytrade_token || "");
      setBingxApiKey(profile.broker_accounts?.bingx_api_key || "");
      setBingxSecret(profile.broker_accounts?.bingx_secret || "");
    }
  }, [profile, user]);

  useEffect(() => {
    if (isSuperAdmin) {
      loadRegisteredUsers();
      void cargarConfigIA();
    }
  }, [isSuperAdmin, cargarConfigIA]);

  const handleGuardarIA = async () => {
    setIaGuardando(true);
    setIaMensaje(null);
    setIaPruebaResultado(null);
    try {
      const guardado = await saveIAProveedor({
        nombre: iaNombre,
        endpoint: iaEndpoint,
        modelo: iaModelo,
        api_key: iaApiKey || undefined,
      });
      setIaTieneClave(guardado.tiene_clave);
      setIaApiKey("");
      setIaMensaje("Configuración guardada en el servidor sin exponer la clave.");
    } catch (err: any) {
      setIaMensaje(`Error al guardar: ${err?.message || err}`);
    } finally {
      setIaGuardando(false);
    }
  };

  const handleProbarIA = async () => {
    setIaProbando(true);
    setIaPruebaResultado(null);
    try {
      const res = await probarIAProveedor();
      setIaPruebaResultado(res);
    } catch (err: any) {
      setIaPruebaResultado({
        ok: false,
        status_code: 500,
        detalle: err?.message || "Error al conectar con la API local.",
      });
    } finally {
      setIaProbando(false);
    }
  };

  const loadRegisteredUsers = async () => {
    setLoadingUsers(true);
    try {
      const list = await listAllUsers();
      setManagedUsers(list);
    } catch (e) {
      console.error("Error loading users:", e);
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleAuthorize = async (targetUid: string, targetEmail: string) => {
    setAdminActionMsg(null);
    try {
      await authorizeUser(targetUid, "trader");
      setAdminActionMsg(`Usuario ${targetEmail} autorizado exitosamente.`);
      await loadRegisteredUsers();
    } catch (err: any) {
      setErrorMessage(err?.message || "Error al autorizar usuario.");
    }
  };

  const handleRevoke = async (targetUid: string, targetEmail: string) => {
    setAdminActionMsg(null);
    try {
      await revokeUser(targetUid);
      setAdminActionMsg(`Acceso de ${targetEmail} revocado.`);
      await loadRegisteredUsers();
    } catch (err: any) {
      setErrorMessage(err?.message || "Error al revocar usuario.");
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);
    setSaving(true);

    try {
      await updateUserProfile({
        displayName: displayName.trim(),
        preferences: {
          ...profile?.preferences,
          default_asset: defaultAsset,
          notifications,
          theme: "dark",
        },
        broker_accounts: {
          ...profile?.broker_accounts,
          tradovate_account_id: tradovateId.trim(),
          ninjatrader_account_id: ninjatraderId.trim(),
          pickmytrade_token: pickmytradeToken.trim(),
          bingx_api_key: bingxApiKey.trim(),
          bingx_secret: bingxSecret.trim(),
        },
      });
      setSuccessMessage("¡Perfil y credenciales de broker guardados exitosamente en Firestore!");
    } catch (err: any) {
      setErrorMessage(err?.message || "Error al actualizar el perfil.");
    } finally {
      setSaving(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-2 text-[var(--text-2)] text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-[var(--text-2)]" />
          <span>Cargando datos de perfil...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[65vh] p-4 text-center">
        <div className="max-w-md w-full bg-[var(--surface-1)] border border-white/[0.1] rounded-2xl p-8 backdrop-blur-xl shadow-2xl">
          <div className="w-12 h-12 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] flex items-center justify-center mx-auto mb-4">
            <User className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-[var(--text-1)] mb-2">Acceso Requerido</h2>
          <p className="text-xs text-[var(--text-2)] mb-6 leading-relaxed">
            Inicia sesión o regístrate para acceder y gestionar tus configuraciones de usuario y claves de brokers.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-1)] text-xs font-bold rounded-xl transition-all shadow-lg "
          >
            <LogIn className="w-4 h-4" />
            <span>Iniciar Sesión</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4 pb-8">
      {/* Header Banner */}
      <div className="p-5 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt={displayName || "User"}
                className="w-12 h-12 rounded-lg object-cover border border-[var(--border-strong)]"
              />
            ) : (
              <div className="w-12 h-12 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-1)] font-bold text-lg flex items-center justify-center">
                {isSuperAdmin ? <Crown className="w-6 h-6 text-[var(--text-1)]" /> : (displayName || user.email || "U").charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-lg font-bold text-[var(--text-1)] tracking-tight">
                  {displayName || "Trader"}
                </h1>
                {isSuperAdmin ? (
                  <span className="px-2.5 py-0.5 rounded-lg bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-1)] text-[10.5px] font-mono font-bold flex items-center gap-1 shadow-[0_0_12px_rgba(255,255,255,0.06)]">
                    <Crown className="w-3.5 h-3.5 text-[var(--text-2)]" />
                    SUPER ADMIN (ACCESO TOTAL)
                  </span>
                ) : isAuthorized ? (
                  <span className="px-2 py-0.5 rounded bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-[10.5px] font-mono font-semibold">
                    USUARIO AUTORIZADO
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-2)] text-[10.5px] font-mono font-semibold">
                    PENDIENTE DE APROBACIÓN
                  </span>
                )}
              </div>
              <p className="text-xs text-[var(--text-2)] font-mono mt-0.5">{user.email}</p>
              <p className="text-[11px] text-[var(--text-3)] font-mono mt-1">
                UID: {user.uid}
              </p>
            </div>
          </div>

          <div className="flex sm:flex-col items-end gap-1.5 font-mono text-[11px] text-[var(--text-2)]">
            <div>
              Último login: <span className="text-[var(--text-1)] font-semibold">{profile?.last_login ? new Date(profile.last_login).toLocaleString("es-ES") : "Ahora"}</span>
            </div>
            <div>
              Alta cuenta: <span className="text-[var(--text-1)] font-semibold">{profile?.created_at ? new Date(profile.created_at).toLocaleDateString("es-ES") : "Reciente"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Non-authorized warning banner */}
      {!isAuthorized && (
        <div className="p-4 rounded-xl bg-[var(--surface-2)] border border-[var(--border)] text-[var(--text-1)] text-xs flex items-start gap-3 shadow-lg font-mono">
          <AlertCircle className="w-5 h-5 text-[var(--text-2)] flex-shrink-0 mt-0.5" />
          <div className="space-y-1 font-sans">
            <p className="font-bold text-[var(--text-1)]">Cuenta en Espera de Autorización</p>
            <p className="text-xs text-[var(--text-1)]">
              Tu cuenta está registrada en Firebase. Por política de gobernanza Zero-Trust, el Super Administrador (<strong className="text-[var(--text-1)]">{SUPERADMIN_EMAIL}</strong>) debe autorizar tu acceso para operar en los módulos de Trading Desk y Bóveda Cuantitativa.
            </p>
          </div>
        </div>
      )}

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)] text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[var(--loss)]" />
          <div className="flex-1 font-medium">{errorMessage}</div>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-xs flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[var(--profit)]" />
          <div className="flex-1 font-medium">{successMessage}</div>
        </div>
      )}

      {/* SECTION: SUPER ADMIN USER MANAGEMENT PANEL (ONLY VISIBLE TO JOSFERESTUDIO) */}
      {isSuperAdmin && (
        <div className="p-4 bg-[var(--surface-1)] border border-[var(--border)] rounded-lg space-y-3">
          <div className="flex items-center justify-between border-b border-[var(--border)] pb-2.5">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-[var(--text-2)]" />
              <h2 className="text-xs font-bold text-[var(--text-1)] uppercase tracking-wider font-mono">
                Panel de Gobernanza Super Admin: Autorización de Usuarios Firebase
              </h2>
            </div>
            <button
              onClick={loadRegisteredUsers}
              disabled={loadingUsers}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--surface-1)] hover:bg-[var(--surface-1)] text-[var(--text-1)] text-xs font-mono transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingUsers ? "animate-spin text-[var(--text-2)]" : ""}`} />
              <span>Refrescar</span>
            </button>
          </div>

          {adminActionMsg && (
            <div className="p-3 rounded-xl bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[var(--profit)]" />
              <span>{adminActionMsg}</span>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-[var(--text-1)] font-mono">
              <thead className="bg-[var(--surface-1)] text-[var(--text-2)] text-[10.5px] uppercase border-b border-white/[0.08]">
                <tr>
                  <th className="py-2.5 px-3">Usuario / Email</th>
                  <th className="py-2.5 px-3">Rol</th>
                  <th className="py-2.5 px-3">Estado</th>
                  <th className="py-2.5 px-3">Fecha Registro</th>
                  <th className="py-2.5 px-3 text-right">Acción Super Admin</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05]">
                {managedUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-[var(--text-3)]">
                      No hay usuarios registrados pendientes.
                    </td>
                  </tr>
                ) : (
                  managedUsers.map((u) => {
                    const isSelf = isSuperAdminEmail(u.email);
                    const isAuth = u.status === "AUTHORIZED" || u.is_authorized === true;

                    return (
                      <tr key={u.uid} className="hover:bg-white/[0.02]">
                        <td className="py-3 px-3">
                          <span className="font-bold text-[var(--text-1)] block">{u.displayName || u.email?.split("@")[0]}</span>
                          <span className="text-[10px] text-[var(--text-3)]">{u.email}</span>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isSelf
                              ? "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)]"
                              : "bg-[var(--surface-1)] text-[var(--text-1)]"
                          }`}>
                            {isSelf ? "SUPERADMIN" : (u.role || "PENDING").toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isAuth
                              ? "bg-[var(--profit-dim)] text-[var(--profit)] border border-[var(--profit)]"
                              : "bg-[var(--surface-2)] text-[var(--text-1)] border border-[var(--border)]"
                          }`}>
                            {isAuth ? "AUTORIZADO" : "PENDIENTE"}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-[11px] text-[var(--text-2)]">
                          {u.created_at ? new Date(u.created_at).toLocaleDateString("es-ES") : "Reciente"}
                        </td>
                        <td className="py-3 px-3 text-right">
                          {isSelf ? (
                            <span className="text-[10px] text-[var(--text-3)] italic">Propietario Base</span>
                          ) : isAuth ? (
                            <button
                              onClick={() => handleRevoke(u.uid, u.email || u.uid)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[var(--loss-dim)] hover:bg-[var(--loss-dim)] border border-[var(--loss)] text-[var(--loss)] text-[11px] transition"
                            >
                              <UserX className="w-3 h-3 text-[var(--loss)]" />
                              <span>Revocar</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleAuthorize(u.uid, u.email || u.uid)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[var(--profit-dim)] hover:bg-[var(--profit-dim)] border border-[var(--profit)] text-[var(--profit)] text-[11px] font-bold transition shadow-sm"
                            >
                              <UserCheck className="w-3 h-3 text-[var(--profit)]" />
                              <span>Autorizar</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* PANEL DE CONFIGURACIÓN DEL PROVEEDOR DE IA (SUPER ADMIN) */}
          <div id="config-ia" className="mt-4 pt-4 border-t border-[var(--border)] space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-2.5">
              <div className="flex items-center gap-2">
                <Bot className="w-4 h-4 text-[var(--profit)]" />
                <h2 className="text-xs font-bold text-[var(--text-1)] uppercase tracking-wider font-mono">
                  Proveedor de IA (Hermes / Antigravity / OpenAI-Compatible)
                </h2>
              </div>
              <span className="text-[10px] text-[var(--text-3)] font-mono">
                Almacenado seguro en servidor (~/.ultrarentable/ia_config.json)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
              <div>
                <label className="block text-[11px] text-[var(--text-3)] mb-1">
                  Nombre del Proveedor (para reconocerlo)
                </label>
                <input
                  type="text"
                  value={iaNombre}
                  onChange={(e) => setIaNombre(e.target.value)}
                  placeholder="Ej. Hermes 3.8 Flash / Antigravity Flash"
                  className="w-full px-3 py-1.5 bg-[var(--surface-2)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded text-xs text-[var(--text-1)] outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] text-[var(--text-3)] mb-1">
                  Dirección del Endpoint (URL)
                </label>
                <input
                  type="text"
                  value={iaEndpoint}
                  onChange={(e) => setIaEndpoint(e.target.value)}
                  placeholder="Ej. http://127.0.0.1:8129/v1 o https://..."
                  className="w-full px-3 py-1.5 bg-[var(--surface-2)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded text-xs text-[var(--text-1)] outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] text-[var(--text-3)] mb-1">
                  Modelo
                </label>
                <input
                  type="text"
                  value={iaModelo}
                  onChange={(e) => setIaModelo(e.target.value)}
                  placeholder="Ej. gemini-2.0-flash / qwen-turbo"
                  className="w-full px-3 py-1.5 bg-[var(--surface-2)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded text-xs text-[var(--text-1)] outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] text-[var(--text-3)] mb-1">
                  Clave API (se guarda en el servidor, no viaja al navegador)
                </label>
                <input
                  type="password"
                  value={iaApiKey}
                  onChange={(e) => setIaApiKey(e.target.value)}
                  placeholder={iaTieneClave ? "•••••••••••• (clave ya configurada en el servidor)" : "Clave secreta"}
                  className="w-full px-3 py-1.5 bg-[var(--surface-2)] border border-[var(--border)] focus:border-[var(--border-strong)] rounded text-xs text-[var(--text-1)] outline-none"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[var(--border)]">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleGuardarIA}
                  disabled={iaGuardando}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border-strong)] text-xs text-[var(--text-1)] font-bold transition cursor-pointer disabled:opacity-50"
                >
                  {iaGuardando ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  <span>Guardar configuración</span>
                </button>

                <button
                  type="button"
                  onClick={handleProbarIA}
                  disabled={iaProbando || !iaEndpoint}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--surface-2)] hover:bg-[var(--surface-3)] border border-[var(--border)] text-xs text-[var(--text-2)] hover:text-[var(--text-1)] font-bold transition cursor-pointer disabled:opacity-50"
                >
                  {iaProbando ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                  <span>Probar conexión</span>
                </button>
              </div>

              {iaMensaje && (
                <span className="text-[11px] text-[var(--profit)] font-mono">
                  {iaMensaje}
                </span>
              )}
            </div>

            {/* Resultado de la Prueba de Conexión Real */}
            {iaPruebaResultado && (
              <div
                className={`p-3 rounded border text-xs leading-relaxed space-y-1 font-mono ${
                  iaPruebaResultado.ok
                    ? "bg-[var(--profit-dim)] border-[var(--profit)] text-[var(--profit)]"
                    : "bg-[var(--loss-dim)] border-[var(--loss)] text-[var(--loss)]"
                }`}
              >
                <div className="flex items-center gap-2 font-bold">
                  <span>Resultado de llamada real: HTTP {iaPruebaResultado.status_code}</span>
                  <span>({iaPruebaResultado.ok ? "Conectado correctamente" : "Fallo de conexión"})</span>
                </div>
                <p className="text-[11px] text-[var(--text-1)] break-all whitespace-pre-wrap">
                  {iaPruebaResultado.detalle}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Asistente de IA (Antigravity / Hermes) */}
      <AsistenteIA />

      {/* Configuración Central de Motores (A52 - StrategyQuant M1) */}
      <ConfiguracionMotores />

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Preferencias de Usuario */}
        <div className="p-5 bg-[var(--surface-1)] border border-white/[0.08] rounded-2xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/[0.06] pb-3">
            <Sliders className="w-4 h-4 text-[var(--text-2)]" />
            <h2 className="text-sm font-bold text-[var(--text-1)] tracking-wide">
              Información General & Preferencias
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                Nombre de Usuario / Alias
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Nombre para la plataforma"
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--border)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                Activo / Futuro Principal por Defecto
              </label>
              <select
                value={defaultAsset}
                onChange={(e) => setDefaultAsset(e.target.value)}
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--border)] rounded-xl text-xs text-[var(--text-1)] outline-none"
              >
                <option value="NQ">E-mini NASDAQ 100 (NQ / MNQ)</option>
                <option value="ES">E-mini S&P 500 (ES / MES)</option>
                <option value="GC">Gold Futures (GC / MGC)</option>
                <option value="CL">Crude Oil (CL / MCL)</option>
                <option value="BTCUSDT">Bitcoin Perp (BingX)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 2: Conexión de Cuentas de Broker */}
        <div className="p-5 bg-[var(--surface-1)] border border-white/[0.08] rounded-2xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/[0.06] pb-3">
            <Server className="w-4 h-4 text-[var(--profit)]" />
            <h2 className="text-sm font-bold text-[var(--text-1)] tracking-wide">
              Conectores de Brokers & Prop Firms (Sincronización Firestore)
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tradovate */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                Tradovate Account ID
              </label>
              <input
                type="text"
                value={tradovateId}
                onChange={(e) => setTradovateId(e.target.value)}
                placeholder="TRADO-123456"
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none font-mono"
              />
            </div>

            {/* NinjaTrader */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                NinjaTrader Account ID
              </label>
              <input
                type="text"
                value={ninjatraderId}
                onChange={(e) => setNinjatraderId(e.target.value)}
                placeholder="NT-SIM-9988"
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none font-mono"
              />
            </div>

            {/* PickMyTrade */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                PickMyTrade Webhook / Token
              </label>
              <input
                type="password"
                value={pickmytradeToken}
                onChange={(e) => setPickmytradeToken(e.target.value)}
                placeholder="pmt_live_sec_..."
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none font-mono"
              />
            </div>

            {/* BingX API Key */}
            <div>
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                BingX API Key (Track ULTRA)
              </label>
              <input
                type="text"
                value={bingxApiKey}
                onChange={(e) => setBingxApiKey(e.target.value)}
                placeholder="bingx_api_key_..."
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none font-mono"
              />
            </div>

            {/* BingX Secret */}
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-[var(--text-1)] mb-1.5 font-mono">
                BingX Secret Key
              </label>
              <input
                type="password"
                value={bingxSecret}
                onChange={(e) => setBingxSecret(e.target.value)}
                placeholder="bingx_secret_key_..."
                className="w-full px-3.5 py-2 bg-[var(--surface-1)] border border-white/[0.08] focus:border-[var(--profit)] rounded-xl text-xs text-[var(--text-1)] placeholder-[var(--text-3)] outline-none font-mono"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2 px-5 bg-[var(--surface-3)] hover:bg-[var(--surface-2)] border border-[var(--border-strong)] text-[var(--text-1)] text-xs font-semibold rounded-md transition-all cursor-pointer disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Guardando en Firestore...</span>
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>Guardar Cambios</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
