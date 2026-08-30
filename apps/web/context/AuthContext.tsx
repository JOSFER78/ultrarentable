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
  doc,
  getDoc,
  setDoc,
  updateDoc,
} from "firebase/firestore";
import { auth, db, googleProvider } from "@/lib/firebase";

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
  role?: "trader" | "quant" | "admin" | string;
  preferences?: UserPreferences;
  broker_accounts?: BrokerAccounts;
  trading_accounts?: BrokerAccounts;
  [key: string]: any;
}

export interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  updateUserProfile: (data: Partial<UserProfile>) => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Sync / fetch profile from Firestore
  const syncUserProfile = async (firebaseUser: User, customDisplayName?: string): Promise<UserProfile> => {
    const userDocRef = doc(db, "users", firebaseUser.uid);
    const nowIso = new Date().toISOString();

    try {
      const docSnap = await getDoc(userDocRef);
      if (docSnap.exists()) {
        const existingData = docSnap.data() as UserProfile;
        const updatedProfile: UserProfile = {
          ...existingData,
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: customDisplayName || existingData.displayName || firebaseUser.displayName || "",
          photoURL: firebaseUser.photoURL || existingData.photoURL || null,
          last_login: nowIso,
        };
        await setDoc(userDocRef, { last_login: nowIso, displayName: updatedProfile.displayName }, { merge: true });
        return updatedProfile;
      } else {
        const newProfile: UserProfile = {
          uid: firebaseUser.uid,
          email: firebaseUser.email,
          displayName: customDisplayName || firebaseUser.displayName || "",
          photoURL: firebaseUser.photoURL || null,
          created_at: nowIso,
          last_login: nowIso,
          role: "trader",
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
        await setDoc(userDocRef, newProfile);
        return newProfile;
      }
    } catch (error) {
      console.error("Error syncing user profile in Firestore:", error);
      // Fallback local profile if Firestore fails offline
      return {
        uid: firebaseUser.uid,
        email: firebaseUser.email,
        displayName: customDisplayName || firebaseUser.displayName || "",
        photoURL: firebaseUser.photoURL || null,
        created_at: nowIso,
        last_login: nowIso,
        role: "trader",
        preferences: { theme: "dark", notifications: true },
        broker_accounts: {},
      };
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        setUser(firebaseUser);
        try {
          const userProf = await syncUserProfile(firebaseUser);
          setProfile(userProf);
        } catch (err) {
          console.error("Failed to load user profile:", err);
        }
      } else {
        setUser(null);
        setProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
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
        await updateProfile(userCredential.user, { displayName: displayName.trim() });
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
      const userProf = await syncUserProfile(userCredential.user);
      setUser(userCredential.user);
      setProfile(userProf);
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
    const userDocRef = doc(db, "users", user.uid);
    await setDoc(userDocRef, data, { merge: true });

    if (data.displayName && data.displayName !== user.displayName) {
      await updateProfile(user, { displayName: data.displayName });
    }

    setProfile((prev) => (prev ? { ...prev, ...data } : null));
  };

  const refreshProfile = async () => {
    if (user) {
      const userProf = await syncUserProfile(user);
      setProfile(userProf);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        login,
        register,
        loginWithGoogle,
        logout,
        updateUserProfile,
        refreshProfile,
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
