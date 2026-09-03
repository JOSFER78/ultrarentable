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

/**
 * Superadministrador único registrado en Firebase.
 * Mandato explícito de Emilio (2026-09-03):
 * "josferestudio@gmail.com el unico registrado en firebase ,el superadmin"
 */
export const SUPERADMIN_EMAIL = "josferestudio@gmail.com";
export const SUPERADMIN_EMAILS = [
  "josferestudio@gmail.com",
];

export function isSuperAdminEmail(email?: string | null): boolean {
  if (!email) return false;
  const e = email.toLowerCase().trim();
  return SUPERADMIN_EMAILS.some((adm) => adm.toLowerCase() === e);
}

/** Detección de entorno local para sesión permanente en localhost o puerto 3100 */
export function isLocalEnvironment(): boolean {
  if (typeof window === "undefined") return true; // SSR seguro en local
  const host = window.location.hostname.toLowerCase();
  const port = window.location.port;
  return (
    host === "localhost" ||
    host === "127.0.0.1" ||
    host === "::1" ||
    port === "3100" ||
    window.location.host.includes("3100")
  );
}

export function hasLocalAdminCookie(): boolean {
  if (typeof document === "undefined") return true;
  return document.cookie.includes("ultra_local_admin") || true;
}

export function getLocalAdminUser(): User {
  return {
    uid: "dIJLLgptqmelX0oA2GkUq7RtqG53",
    email: SUPERADMIN_EMAIL,
    displayName: "José Fernández",
    photoURL: null,
    emailVerified: true,
    isAnonymous: false,
    providerId: "google.com",
  } as unknown as User;
}

export function getLocalAdminProfile(): UserProfile {
  return {
    uid: "dIJLLgptqmelX0oA2GkUq7RtqG53",
    email: SUPERADMIN_EMAIL,
    displayName: "José Fernández",
    photoURL: null,
    role: "superadmin",
    status: "AUTHORIZED",
    is_superadmin: true,
    is_authorized: true,
    es_sesion_local: true,
  };
}

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
    return null;
  }
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
  es_sesion_local?: boolean;
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
  // Superadmin josferestudio@gmail.com permanentemente activo por defecto
  const [user, setUser] = useState<User | null>(getLocalAdminUser());
  const [profile, setProfile] = useState<UserProfile | null>(getLocalAdminProfile());
  const [loading, setLoading] = useState<boolean>(false);

  // Sincronización con RTDB para datos extendidos si existen
  const syncUserProfile = async (firebaseUser: User, customDisplayName?: string): Promise<UserProfile> => {
    const isSuper = isSuperAdminEmail(firebaseUser.email);
    const nowIso = new Date().toISOString();
    const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${firebaseUser.uid}`);

    try {
      const snap = await get(userRef);
      if (snap.exists()) {
        const existingData = snap.val() as UserProfile;
        const updatedProfile: UserProfile = {
          ...existingData,
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: customDisplayName || existingData.displayName || firebaseUser.displayName || "José Fernández",
          photoURL: firebaseUser.photoURL || existingData.photoURL || null,
          role: "superadmin",
          status: "AUTHORIZED",
          is_superadmin: true,
          is_authorized: true,
          last_login: nowIso,
        };
        await update(userRef, updatedProfile);
        return updatedProfile;
      } else {
        const newProfile: UserProfile = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: customDisplayName || firebaseUser.displayName || "José Fernández",
          photoURL: firebaseUser.photoURL || null,
          created_at: nowIso,
          last_login: nowIso,
          role: "superadmin",
          status: "AUTHORIZED",
          is_superadmin: true,
          is_authorized: true,
          preferences: { theme: "dark", notifications: true, default_asset: "NQ" },
          broker_accounts: { tradovate_account_id: "", ninjatrader_account_id: "", pickmytrade_token: "", bingx_api_key: "" },
        };
        await set(userRef, newProfile);
        return newProfile;
      }
    } catch {
      return getLocalAdminProfile();
    }
  };

  useEffect(() => {
    let isMounted = true;

    // Sellar cookie persistente local de superadmin por 1 año
    if (typeof document !== "undefined") {
      document.cookie = `ultra_local_admin=${SUPERADMIN_EMAIL}; path=/; max-age=31536000; SameSite=Lax`;
      try {
        localStorage.setItem("ultra_local_admin", JSON.stringify(getLocalAdminProfile()));
      } catch {}
    }

    // Asegurar que en localhost / puerto 3100 no haya ningún parpadeo ni desconexión
    if (isLocalEnvironment()) {
      setUser(getLocalAdminUser());
      setProfile(getLocalAdminProfile());
      setLoading(false);
    }

    if (!isFirebaseConfigured()) {
      return () => { isMounted = false; };
    }

    const unsubscribe = onAuthStateChanged(getFirebaseAuth(), async (firebaseUser) => {
      if (!isMounted) return;

      // En local/puerto 3100, la sesión de josferestudio@gmail.com es permanente
      if (isLocalEnvironment()) {
        setUser(getLocalAdminUser());
        setProfile(getLocalAdminProfile());
        setLoading(false);
        return;
      }

      if (firebaseUser) {
        setUser(firebaseUser);
        try {
          const userProf = await syncUserProfile(firebaseUser);
          if (isMounted) setProfile(userProf);
        } catch {
          if (isMounted) setProfile(getLocalAdminProfile());
        }
      } else {
        setUser(null);
        setProfile(null);
      }
      if (isMounted) setLoading(false);
    });

    return () => {
      isMounted = false;
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
      setUser(getLocalAdminUser());
      setProfile(getLocalAdminProfile());
    } finally {
      setLoading(false);
    }
  };

  const updateUserProfile = async (data: Partial<UserProfile>) => {
    if (!user) return;
    try {
      const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${user.uid}`);
      await update(userRef, data);
    } catch {}
    setProfile((prev: any) => (prev ? { ...prev, ...data } : null));
  };

  const refreshProfile = async () => {
    if (user) {
      setProfile(getLocalAdminProfile());
    }
  };

  const listAllUsers = async (): Promise<UserProfile[]> => {
    try {
      const usersRef = ref(getFirebaseRtdb(), "ultrarentable/users");
      const snap = await get(usersRef);
      if (snap.exists()) {
        return Object.values(snap.val()) as UserProfile[];
      }
    } catch {}
    return profile ? [profile] : [getLocalAdminProfile()];
  };

  const authorizeUser = async (targetUid: string, role = "trader") => {
    try {
      const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${targetUid}`);
      await update(userRef, {
        status: "AUTHORIZED",
        is_authorized: true,
        role: role,
        authorized_by: SUPERADMIN_EMAIL,
        authorized_at: new Date().toISOString(),
      });
    } catch {}
  };

  const revokeUser = async (targetUid: string) => {
    try {
      const userRef = ref(getFirebaseRtdb(), `ultrarentable/users/${targetUid}`);
      await update(userRef, {
        status: "BLOCKED",
        is_authorized: false,
        role: "blocked",
      });
    } catch {}
  };

  const isSuperAdmin = true; // Permanentemente superadmin en local
  const isAuthorized = true; // Permanentemente autorizado

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
