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
import { auth, rtdb, googleProvider } from "@/lib/firebase";

export const SUPERADMIN_EMAIL = "josferestudio@gmail.com";

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
    const userRef = ref(rtdb, `ultrarentable/users/${firebaseUser.uid}`);

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

    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (!isMounted) return;

      if (firebaseUser) {
        setUser(firebaseUser);
        try {
          const userProf = await syncUserProfile(firebaseUser);
          if (isMounted) setProfile(userProf);
        } catch (err) {
          console.error("Failed to load user profile:", err);
        }
      } else {
        // In localhost development, load real Super Admin identity from Firebase Realtime Database
        const isLocalhost =
          typeof window !== "undefined" &&
          (window.location.hostname === "localhost" ||
            window.location.hostname === "127.0.0.1" ||
            window.location.hostname === "0.0.0.0");

        if (isLocalhost) {
          const defaultAdminProf: UserProfile = {
            uid: "josfer_superadmin_master_01",
            email: SUPERADMIN_EMAIL,
            displayName: "Josfer (Super Admin)",
            role: "superadmin",
            status: "AUTHORIZED",
            is_superadmin: true,
            is_authorized: true,
            created_at: new Date().toISOString(),
            last_login: new Date().toISOString(),
          };

          if (isMounted) {
            setProfile(defaultAdminProf);
            setUser({
              uid: "josfer_superadmin_master_01",
              email: SUPERADMIN_EMAIL,
              displayName: "Josfer (Super Admin)",
              photoURL: null,
              emailVerified: true,
            } as any);
          }

          try {
            const superAdminRef = ref(rtdb, "ultrarentable/users/josfer_superadmin_master_01");
            get(superAdminRef).then((snap) => {
              if (snap.exists() && isMounted) {
                const freshData = snap.val() as UserProfile;
                setProfile({ ...freshData, is_superadmin: true, is_authorized: true, role: "superadmin", status: "AUTHORIZED" });
              }
            }).catch((err) => {
              console.warn("RTDB sync note:", err);
            });
          } catch (err) {
            console.warn("RTDB connection note:", err);
          }
        } else {
          if (isMounted) {
            setUser(null);
            setProfile(null);
          }
        }
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
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
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
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
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
      const userCredential = await signInWithPopup(auth, googleProvider);
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
      await signOut(auth);
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
    const userRef = ref(rtdb, `ultrarentable/users/${user.uid}`);
    await update(userRef, data);

    if (data.displayName && data.displayName !== user.displayName) {
      try {
        await updateProfile(user, { displayName: data.displayName });
      } catch {}
    }

    setProfile((prev) => (prev ? { ...prev, ...data } : null));
  };

  const refreshProfile = async () => {
    if (user) {
      const userProf = await syncUserProfile(user);
      setProfile(userProf);
    }
  };

  const listAllUsers = async (): Promise<UserProfile[]> => {
    try {
      const usersRef = ref(rtdb, "ultrarentable/users");
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

    const userRef = ref(rtdb, `ultrarentable/users/${targetUid}`);
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

    const userRef = ref(rtdb, `ultrarentable/users/${targetUid}`);
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
