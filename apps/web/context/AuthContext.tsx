"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import {
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
  onAuthStateChanged,
} from "firebase/auth";
import {
  ref,
  get,
  set,
  update,
} from "firebase/database";
import {
  auth,
  rtdb,
  googleProvider,
  getFirebaseAuth,
  getFirebaseRtdb,
  getGoogleProvider,
  isFirebaseConfigured,
  missingFirebaseEnvVars,
} from "@/lib/firebase";

export const SUPERADMIN_EMAIL = "josferestudio@gmail.com";

/**
 * Sesion permanente del superadministrador en la instancia LOCAL (localhost:3100).
 *
 * Quien la autoriza es el SERVIDOR, no el navegador: `app/api/local/superadmin/route.ts` solo
 * responde `enabled:true` si el proceso que sirve la web tiene ULTRARENTABLE_LOCAL_SUPERADMIN=1
 * (variable de `apps/web/.env.local`, que no se versiona) Y ademas la peticion llega a un host
 * local. El VPS sirve el MISMO build sin esa variable, asi que alli no se activa nunca y el
 * acceso publico sigue pasando por Firebase.
 *
 * No sustituye a Firebase: si hay un usuario de Firebase de verdad, manda ese. La sesion local
 * solo entra cuando no hay ninguno.
 */
export interface SesionLocalSuperadmin {
  enabled: boolean;
  email?: string;
  uid?: string;
  displayName?: string;
  motivo?: string;
}

async function consultarSesionLocal(): Promise<SesionLocalSuperadmin | null> {
  try {
    const res = await fetch("/api/local/superadmin", { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as SesionLocalSuperadmin;
  } catch {
    return null; // sin respuesta no se asume nada: se queda la pantalla de login normal
  }
}

/** Usuario minimo para la sesion local. La UI solo usa email, uid y photoURL (comprobado con
 * grep sobre apps/web: no se llama a getIdToken en ninguna parte), asi que no se simula un
 * usuario de Firebase completo: se marca claramente como sesion local. */
function usuarioDeSesionLocal(s: SesionLocalSuperadmin): User {
  return {
    uid: s.uid || "local-superadmin",
    email: s.email || SUPERADMIN_EMAIL,
    displayName: s.displayName || "Super Admin (sesion local)",
    photoURL: null,
    emailVerified: true,
    isAnonymous: false,
    providerId: "local",
  } as unknown as User;
}

function perfilDeSesionLocal(s: SesionLocalSuperadmin): UserProfile {
  return {
    uid: s.uid || "local-superadmin",
    email: s.email || SUPERADMIN_EMAIL,
    displayName: s.displayName || "Super Admin (sesion local)",
    photoURL: null,
    role: "superadmin",
    status: "AUTHORIZED",
    is_superadmin: true,
    is_authorized: true,
    // Marca honesta: este perfil no viene de Firebase ni de la base de datos, viene de que el
    // servidor local dice que esta maquina es la de Emilio.
    es_sesion_local: true,
  };
}

export interface BrokerAccounts {
  tradovate_account_id?: string;
  ninjatrader_account_id?: string;
  pickmytrade_token?: string;
  gateway_webhook_token?: string;
  broker?: string;
  environment?: "DEMO" | "LIVE" | string;
  bingx_api_key?: string;
  bingx_secret?: string;
  updated_at?: string;
  [key: string]: any;
}

export interface UserPreferences {
  theme?: "dark" | "light" | "system";
  notifications?: boolean;
  default_asset?: string;
  risk_limit_per_day?: number;
  [key: string]: any;
}

export interface UserProfile {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL?: string | null;
  created_at?: string;
  last_login?: string;
  role?: "superadmin" | "admin" | "quant" | "trader" | "pending" | string;
  status?: "AUTHORIZED" | "PENDING_APPROVAL" | "BLOCKED" | string;
  is_superadmin?: boolean;
  is_authorized?: boolean;
  authorized_by?: string;
  authorized_at?: string;
  preferences?: UserPreferences;
  broker_accounts?: BrokerAccounts;
  trading_accounts?: BrokerAccounts;
  [key: string]: any;
}

export interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  isSuperAdmin: boolean;
  isAuthorized: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  updateUserProfile: (data: Partial<UserProfile>) => Promise<void>;
  refreshProfile: () => Promise<void>;
  listAllUsers: () => Promise<UserProfile[]>;
  authorizeUser: (targetUid: string, role?: string) => Promise<void>;
  revokeUser: (targetUid: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Sync profile using real Firebase Realtime Database
  const syncUserProfile = async (firebaseUser: User, customDisplayName?: string): Promise<UserProfile> => {
    const userEmail = (firebaseUser.email || "").toLowerCase().trim();
    const isSuperAdminEmail = userEmail === SUPERADMIN_EMAIL.toLowerCase();
    const nowIso = new Date().toISOString();
    const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${firebaseUser.uid}`);

    try {
      const snap = await get(userRef);
      if (snap.exists()) {
        const existingData = snap.val() as UserProfile;
        const isAuth = isSuperAdminEmail || existingData.status === "AUTHORIZED" || existingData.is_authorized === true;
        const resolvedRole = isSuperAdminEmail ? "superadmin" : (isAuth ? (existingData.role || "trader") : "pending");
        const resolvedStatus = isSuperAdminEmail ? "AUTHORIZED" : (isAuth ? "AUTHORIZED" : "PENDING_APPROVAL");

        const updatedProfile: UserProfile = {
          ...existingData,
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: customDisplayName || existingData.displayName || firebaseUser.displayName || (isSuperAdminEmail ? "Josfer (Super Admin)" : ""),
          photoURL: firebaseUser.photoURL || existingData.photoURL || null,
          role: resolvedRole,
          status: resolvedStatus,
          is_superadmin: isSuperAdminEmail,
          is_authorized: isAuth,
          last_login: nowIso,
        };

        await update(userRef, {
          last_login: nowIso,
          displayName: updatedProfile.displayName,
          role: resolvedRole,
          status: resolvedStatus,
          is_superadmin: isSuperAdminEmail,
          is_authorized: isAuth,
        });

        return updatedProfile;
      } else {
        // New real user in RTDB
        const isAuth = isSuperAdminEmail;
        const newProfile: UserProfile = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: customDisplayName || firebaseUser.displayName || (isSuperAdminEmail ? "Josfer (Super Admin)" : "Usuario"),
          photoURL: firebaseUser.photoURL || null,
          created_at: nowIso,
          last_login: nowIso,
          role: isSuperAdminEmail ? "superadmin" : "pending",
          status: isSuperAdminEmail ? "AUTHORIZED" : "PENDING_APPROVAL",
          is_superadmin: isSuperAdminEmail,
          is_authorized: isAuth,
          preferences: {
            theme: "dark",
            notifications: true,
            default_asset: "NQ",
          },
          broker_accounts: {
            tradovate_account_id: "",
            ninjatrader_account_id: "",
            pickmytrade_token: "",
            bingx_api_key: "",
          },
        };

        await set(userRef, newProfile);
        return newProfile;
      }
    } catch (error) {
      console.warn("RTDB sync fallback:", error);
      const isAuth = isSuperAdminEmail;
      return {
        uid: firebaseUser.uid,
        email: firebaseUser.email,
        displayName: customDisplayName || firebaseUser.displayName || (isSuperAdminEmail ? "Josfer (Super Admin)" : "Usuario"),
        photoURL: firebaseUser.photoURL || null,
        created_at: nowIso,
        last_login: nowIso,
        role: isSuperAdminEmail ? "superadmin" : "pending",
        status: isSuperAdminEmail ? "AUTHORIZED" : "PENDING_APPROVAL",
        is_superadmin: isSuperAdminEmail,
        is_authorized: isAuth,
      };
    }
  };

  useEffect(() => {
    let isMounted = true;
    let authSettled = false;


    // Watchdog: si Firebase Auth no emite estado (o la carga de perfil se cuelga) en 6s,
    // no se deja al usuario ante un spinner infinito: en localhost se aplica el mismo
    // bypass de Super Admin que ya contempla la rama de desarrollo; fuera de localhost se
    // resuelve a la landing pública (donde puede reintentar el login).
    if (!isFirebaseConfigured()) {
      console.warn("[Auth] Firebase sin configurar: faltan " + missingFirebaseEnvVars().join(", ") + ". Inicio de sesión no disponible hasta rellenar apps/web/.env.local.");
      setUser(null);
      setProfile(null);
      // Firebase sin configurar: la instancia local sigue siendo usable para el superadministrador.
      void consultarSesionLocal().then((local) => {
        if (!isMounted || !local?.enabled) return;
        setUser(usuarioDeSesionLocal(local));
        setProfile(perfilDeSesionLocal(local));
      });
      setLoading(false);
      return () => { isMounted = false; };
    }
    const watchdog = setTimeout(() => {
      if (!isMounted || authSettled) return;
      console.warn("[Auth] Watchdog: Firebase Auth no respondió en 2s; aplicando fallback.");
      setUser(null);
      setProfile(null);
      setLoading(false);
    }, 2000);

    const unsubscribe = onAuthStateChanged(getFirebaseAuth(), async (firebaseUser) => {
      if (!isMounted) return;

      if (firebaseUser) {
        setUser(firebaseUser);
        // Desbloquear estado de carga de inmediato para no congelar la pantalla
        if (isMounted) setLoading(false);
        try {
          const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error("RTDB timeout")), 2500));
          const userProf = await Promise.race([syncUserProfile(firebaseUser), timeoutPromise]) as UserProfile;
          if (isMounted) setProfile(userProf);
        } catch (err) {
          console.warn("User profile sync fallback/timeout:", err);
          if (isMounted && !profile) {
            const userEmail = (firebaseUser.email || "").toLowerCase().trim();
            const isSuperAdminEmail = userEmail === SUPERADMIN_EMAIL.toLowerCase();
            setProfile({
              uid: firebaseUser.uid,
              email: firebaseUser.email,
              displayName: firebaseUser.displayName || (isSuperAdminEmail ? "Josfer (Super Admin)" : "Usuario"),
              photoURL: firebaseUser.photoURL || null,
              role: isSuperAdminEmail ? "superadmin" : "trader",
              status: isSuperAdminEmail ? "AUTHORIZED" : "PENDING_APPROVAL",
              is_superadmin: isSuperAdminEmail,
              is_authorized: isSuperAdminEmail,
            });
          }
        }
      } else {
        // Sin usuario de Firebase: en la instancia local del PC entra el superadministrador de
        // forma permanente (ver consultarSesionLocal). En cualquier otro sitio, sesion cerrada.
        const local = await consultarSesionLocal();
        if (isMounted) {
          if (local?.enabled) {
            setUser(usuarioDeSesionLocal(local));
            setProfile(perfilDeSesionLocal(local));
          } else {
            setUser(null);
            setProfile(null);
          }
          setLoading(false);
        }
      }
      authSettled = true;
      clearTimeout(watchdog);
      if (isMounted) setLoading(false);
    });

    return () => {
      isMounted = false;
      clearTimeout(watchdog);
      unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const userCredential = await signInWithEmailAndPassword(getFirebaseAuth(), email, password);
      const userProf = await syncUserProfile(userCredential.user);
      setUser(userCredential.user);
      setProfile(userProf);
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string, displayName?: string) => {
    setLoading(true);
    try {
      const userCredential = await createUserWithEmailAndPassword(getFirebaseAuth(), email, password);
      if (displayName && displayName.trim()) {
        try {
          await updateProfile(userCredential.user, { displayName: displayName.trim() });
        } catch {}
      }
      const userProf = await syncUserProfile(userCredential.user, displayName?.trim());
      setUser(userCredential.user);
      setProfile(userProf);
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async () => {
    setLoading(true);
    try {
      const authInst = getFirebaseAuth();
      const providerInst = getGoogleProvider();
      const userCredential = await signInWithPopup(authInst, providerInst);
      if (userCredential?.user) {
        const userProf = await syncUserProfile(userCredential.user);
        setUser(userCredential.user);
        setProfile(userProf);
      }
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await signOut(getFirebaseAuth());
      setUser(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const updateUserProfile = async (data: Partial<UserProfile>) => {
    if (!user) {
      throw new Error("No hay una sesión activa para actualizar el perfil.");
    }
    const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${user.uid}`);
    await update(userRef, data);

    if (data.displayName && data.displayName !== user.displayName) {
      try {
        await updateProfile(user, { displayName: data.displayName });
      } catch {}
    }

    setProfile((prev: any) => (prev ? { ...prev, ...data } : null));
  };

  const refreshProfile = async () => {
    if (user) {
      const userProf = await syncUserProfile(user);
      setProfile(userProf);
    }
  };

  const listAllUsers = async (): Promise<UserProfile[]> => {
    try {
      const usersRef = ref(getFirebaseRtdb(), "ultrarentable/users");
      const snap = await get(usersRef);
      if (snap.exists()) {
        const data = snap.val();
        return Object.values(data) as UserProfile[];
      }
    } catch (e) {
      console.warn("Error reading users from RTDB:", e);
    }
    return profile ? [profile] : [];
  };

  const authorizeUser = async (targetUid: string, role = "trader") => {
    const isSuper = profile?.is_superadmin || (user?.email || "").toLowerCase() === SUPERADMIN_EMAIL.toLowerCase();
    if (!isSuper) {
      throw new Error("Acción denegada: Solo el Super Administrador (josferestudio@gmail.com) puede autorizar nuevos usuarios.");
    }

    const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${targetUid}`);
    const nowIso = new Date().toISOString();
    await update(userRef, {
      status: "AUTHORIZED",
      is_authorized: true,
      role: role,
      authorized_by: SUPERADMIN_EMAIL,
      authorized_at: nowIso,
    });
  };

  const revokeUser = async (targetUid: string) => {
    const isSuper = profile?.is_superadmin || (user?.email || "").toLowerCase() === SUPERADMIN_EMAIL.toLowerCase();
    if (!isSuper) {
      throw new Error("Acción denegada: Solo el Super Administrador (josferestudio@gmail.com) puede revocar usuarios.");
    }

    const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${targetUid}`);
    await update(userRef, {
      status: "BLOCKED",
      is_authorized: false,
      role: "blocked",
    });
  };

  const isSuperAdmin = Boolean(
    profile?.is_superadmin ||
    (user?.email || "").toLowerCase() === SUPERADMIN_EMAIL.toLowerCase()
  );

  const isAuthorized = Boolean(
    isSuperAdmin ||
    profile?.is_authorized ||
    profile?.status === "AUTHORIZED"
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        isSuperAdmin,
        isAuthorized,
        login,
        register,
        loginWithGoogle,
        logout,
        updateUserProfile,
        refreshProfile,
        listAllUsers,
        authorizeUser,
        revokeUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return context;
}
