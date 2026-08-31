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
} from "lucide-react";
import { useAuth, UserProfile } from "@/context/AuthContext";

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
    }
  }, [isSuperAdmin]);

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
        <div className="flex items-center gap-2 text-slate-400 text-xs font-mono">
          <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
          <span>Cargando datos de perfil...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[65vh] p-4 text-center">
        <div className="max-w-md w-full bg-[#080d1a]/95 border border-white/[0.1] rounded-2xl p-8 backdrop-blur-xl shadow-2xl">
          <div className="w-12 h-12 rounded-xl bg-sky-500/10 border border-sky-500/30 text-sky-400 flex items-center justify-center mx-auto mb-4">
            <User className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Acceso Requerido</h2>
          <p className="text-xs text-slate-400 mb-6 leading-relaxed">
            Inicia sesión o regístrate para acceder y gestionar tus configuraciones de usuario y claves de brokers.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-sky-500 hover:bg-sky-400 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-sky-500/20"
          >
            <LogIn className="w-4 h-4" />
            <span>Iniciar Sesión</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header Banner */}
      <div className="p-6 bg-gradient-to-br from-[#080d1a] to-[#0d1527] border border-white/[0.08] rounded-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt={displayName || "User"}
                className="w-14 h-14 rounded-2xl object-cover border-2 border-sky-500/40 shadow-lg"
              />
            ) : (
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-emerald-500 text-white font-bold text-xl flex items-center justify-center shadow-lg">
                {isSuperAdmin ? <Crown className="w-7 h-7 text-amber-300" /> : (displayName || user.email || "U").charAt(0).toUpperCase()}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-xl font-bold text-white tracking-tight">
                  {displayName || "Trader"}
                </h1>
                {isSuperAdmin ? (
                  <span className="px-2.5 py-0.5 rounded-lg bg-amber-500/15 border border-amber-500/40 text-amber-300 text-[10.5px] font-mono font-bold flex items-center gap-1 shadow-[0_0_12px_rgba(245,158,11,0.2)]">
                    <Crown className="w-3.5 h-3.5 text-amber-400" />
                    SUPER ADMIN (ACCESO TOTAL)
                  </span>
                ) : isAuthorized ? (
                  <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[10.5px] font-mono font-semibold">
                    USUARIO AUTORIZADO
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[10.5px] font-mono font-semibold">
                    PENDIENTE DE APROBACIÓN
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">{user.email}</p>
              <p className="text-[11px] text-slate-500 font-mono mt-1">
                UID: {user.uid}
              </p>
            </div>
          </div>

          <div className="flex sm:flex-col items-end gap-1.5 font-mono text-[11px] text-slate-400">
            <div>
              Último login: <span className="text-slate-300 font-semibold">{profile?.last_login ? new Date(profile.last_login).toLocaleString("es-ES") : "Ahora"}</span>
            </div>
            <div>
              Alta cuenta: <span className="text-slate-300 font-semibold">{profile?.created_at ? new Date(profile.created_at).toLocaleDateString("es-ES") : "Reciente"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Non-authorized warning banner */}
      {!isAuthorized && (
        <div className="p-4 rounded-xl bg-amber-950/60 border border-amber-500/40 text-amber-200 text-xs flex items-start gap-3 shadow-lg font-mono">
          <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1 font-sans">
            <p className="font-bold text-amber-300">Cuenta en Espera de Autorización</p>
            <p className="text-xs text-amber-200/80">
              Tu cuenta está registrada en Firebase. Por política de gobernanza Zero-Trust, el Super Administrador (<strong className="text-white">josferestudio@gmail.com</strong>) debe autorizar tu acceso para operar en los módulos de Trading Desk y Bóveda Cuantitativa.
            </p>
          </div>
        </div>
      )}

      {/* Notifications */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
          <div className="flex-1 font-medium">{errorMessage}</div>
        </div>
      )}

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-start gap-2.5">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
          <div className="flex-1 font-medium">{successMessage}</div>
        </div>
      )}

      {/* SECTION: SUPER ADMIN USER MANAGEMENT PANEL (ONLY VISIBLE TO JOSFERESTUDIO) */}
      {isSuperAdmin && (
        <div className="p-5 bg-[#080d1a]/95 border border-amber-500/30 rounded-2xl space-y-4 shadow-xl">
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white tracking-wide">
                Panel de Gobernanza Super Admin: Autorización de Usuarios Firebase
              </h2>
            </div>
            <button
              onClick={loadRegisteredUsers}
              disabled={loadingUsers}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingUsers ? "animate-spin text-amber-400" : ""}`} />
              <span>Refrescar</span>
            </button>
          </div>

          {adminActionMsg && (
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{adminActionMsg}</span>
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left text-slate-300 font-mono">
              <thead className="bg-slate-900/80 text-slate-400 text-[10.5px] uppercase border-b border-white/[0.08]">
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
                    <td colSpan={5} className="py-6 text-center text-slate-500">
                      No hay usuarios registrados pendientes.
                    </td>
                  </tr>
                ) : (
                  managedUsers.map((u) => {
                    const isSelf = (u.email || "").toLowerCase() === "josferestudio@gmail.com";
                    const isAuth = u.status === "AUTHORIZED" || u.is_authorized === true;

                    return (
                      <tr key={u.uid} className="hover:bg-white/[0.02]">
                        <td className="py-3 px-3">
                          <span className="font-bold text-white block">{u.displayName || u.email?.split("@")[0]}</span>
                          <span className="text-[10px] text-slate-500">{u.email}</span>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isSelf
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                              : "bg-slate-800 text-slate-300"
                          }`}>
                            {isSelf ? "SUPERADMIN" : (u.role || "PENDING").toUpperCase()}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isAuth
                              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                              : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                          }`}>
                            {isAuth ? "AUTORIZADO" : "PENDIENTE"}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-[11px] text-slate-400">
                          {u.created_at ? new Date(u.created_at).toLocaleDateString("es-ES") : "Reciente"}
                        </td>
                        <td className="py-3 px-3 text-right">
                          {isSelf ? (
                            <span className="text-[10px] text-slate-500 italic">Propietario Base</span>
                          ) : isAuth ? (
                            <button
                              onClick={() => handleRevoke(u.uid, u.email || u.uid)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 text-[11px] transition"
                            >
                              <UserX className="w-3 h-3 text-rose-400" />
                              <span>Revocar</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleAuthorize(u.uid, u.email || u.uid)}
                              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-300 text-[11px] font-bold transition shadow-sm"
                            >
                              <UserCheck className="w-3 h-3 text-emerald-400" />
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
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Section 1: Preferencias de Usuario */}
        <div className="p-5 bg-[#080d1a]/95 border border-white/[0.08] rounded-2xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/[0.06] pb-3">
            <Sliders className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-bold text-white tracking-wide">
              Información General & Preferencias
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                Nombre de Usuario / Alias
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Nombre para la plataforma"
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-sky-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                Activo / Futuro Principal por Defecto
              </label>
              <select
                value={defaultAsset}
                onChange={(e) => setDefaultAsset(e.target.value)}
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-sky-500/50 rounded-xl text-xs text-white outline-none"
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
        <div className="p-5 bg-[#080d1a]/95 border border-white/[0.08] rounded-2xl space-y-4">
          <div className="flex items-center gap-2 border-b border-white/[0.06] pb-3">
            <Server className="w-4 h-4 text-emerald-400" />
            <h2 className="text-sm font-bold text-white tracking-wide">
              Conectores de Brokers & Prop Firms (Sincronización Firestore)
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tradovate */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                Tradovate Account ID
              </label>
              <input
                type="text"
                value={tradovateId}
                onChange={(e) => setTradovateId(e.target.value)}
                placeholder="TRADO-123456"
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-emerald-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none font-mono"
              />
            </div>

            {/* NinjaTrader */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                NinjaTrader Account ID
              </label>
              <input
                type="text"
                value={ninjatraderId}
                onChange={(e) => setNinjatraderId(e.target.value)}
                placeholder="NT-SIM-9988"
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-emerald-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none font-mono"
              />
            </div>

            {/* PickMyTrade */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                PickMyTrade Webhook / Token
              </label>
              <input
                type="password"
                value={pickmytradeToken}
                onChange={(e) => setPickmytradeToken(e.target.value)}
                placeholder="pmt_live_sec_..."
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-emerald-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none font-mono"
              />
            </div>

            {/* BingX API Key */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                BingX API Key (Track ULTRA)
              </label>
              <input
                type="text"
                value={bingxApiKey}
                onChange={(e) => setBingxApiKey(e.target.value)}
                placeholder="bingx_api_key_..."
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-emerald-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none font-mono"
              />
            </div>

            {/* BingX Secret */}
            <div className="md:col-span-2">
              <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono">
                BingX Secret Key
              </label>
              <input
                type="password"
                value={bingxSecret}
                onChange={(e) => setBingxSecret(e.target.value)}
                placeholder="bingx_secret_key_..."
                className="w-full px-3.5 py-2 bg-slate-900/80 border border-white/[0.08] focus:border-emerald-500/50 rounded-xl text-xs text-white placeholder-slate-500 outline-none font-mono"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2.5 px-6 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-500/20 disabled:opacity-50 transition-all cursor-pointer"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Guardando en Firestore...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Guardar Cambios</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
