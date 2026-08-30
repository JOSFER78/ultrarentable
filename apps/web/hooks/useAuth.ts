"use client";

import { useState, useEffect, useCallback } from "react";

export interface UserProfile {
  id?: string;
  name?: string;
  email?: string;
  username?: string;
  account_id?: string;
  role?: string;
}

export interface AuthState {
  user: UserProfile | null;
  accountId: string;
  broker: string | null;
  token: string;
  webhookUrl: string;
  environment: "DEMO" | "LIVE";
  isAuthenticated: boolean;
  isLoading: boolean;
  setAccountId: (accountId: string) => void;
  setToken: (token: string) => void;
  setWebhookUrl: (url: string) => void;
  setEnvironment: (env: "DEMO" | "LIVE") => void;
  logout: () => void;
}

const STORAGE_KEYS = {
  ACCOUNT_ID: "ultrarentable_account_id",
  TOKEN: "ultrarentable_auth_token",
  WEBHOOK_URL: "ultrarentable_webhook_url",
  ENVIRONMENT: "ultrarentable_environment",
  USER: "ultrarentable_user",
};

export function useAuth(): AuthState {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [accountId, setAccountIdState] = useState<string>("");
  const [broker, setBroker] = useState<string | null>(null);
  const [token, setTokenState] = useState<string>("");
  const [webhookUrl, setWebhookUrlState] = useState<string>("");
  const [environment, setEnvironmentState] = useState<"DEMO" | "LIVE">("DEMO");
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize from real browser storage or real gateway settings
  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        const storedAccountId = localStorage.getItem(STORAGE_KEYS.ACCOUNT_ID) || "";
        const storedToken = localStorage.getItem(STORAGE_KEYS.TOKEN) || "";
        const storedWebhook = localStorage.getItem(STORAGE_KEYS.WEBHOOK_URL) || "";
        const storedEnv = (localStorage.getItem(STORAGE_KEYS.ENVIRONMENT) as "DEMO" | "LIVE") || "DEMO";
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);

        if (storedAccountId) setAccountIdState(storedAccountId);
        if (storedToken) setTokenState(storedToken);
        if (storedWebhook) setWebhookUrlState(storedWebhook);
        if (storedEnv) setEnvironmentState(storedEnv);
        if (storedUser) {
          try {
            setUser(JSON.parse(storedUser));
          } catch {
            setUser(null);
          }
        }
      }
    } catch {
      // Storage unavailable or disabled
    } finally {
      setIsLoading(false);
    }
  }, []);

  const setAccountId = useCallback((newId: string) => {
    setAccountIdState(newId);
    if (typeof window !== "undefined") {
      if (newId) {
        localStorage.setItem(STORAGE_KEYS.ACCOUNT_ID, newId);
      } else {
        localStorage.removeItem(STORAGE_KEYS.ACCOUNT_ID);
      }
    }
  }, []);

  const setToken = useCallback((newToken: string) => {
    setTokenState(newToken);
    if (typeof window !== "undefined") {
      if (newToken) {
        localStorage.setItem(STORAGE_KEYS.TOKEN, newToken);
      } else {
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
      }
    }
  }, []);

  const setWebhookUrl = useCallback((newUrl: string) => {
    setWebhookUrlState(newUrl);
    if (typeof window !== "undefined") {
      if (newUrl) {
        localStorage.setItem(STORAGE_KEYS.WEBHOOK_URL, newUrl);
      } else {
        localStorage.removeItem(STORAGE_KEYS.WEBHOOK_URL);
      }
    }
  }, []);

  const setEnvironment = useCallback((newEnv: "DEMO" | "LIVE") => {
    setEnvironmentState(newEnv);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEYS.ENVIRONMENT, newEnv);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setAccountIdState("");
    setTokenState("");
    setWebhookUrlState("");
    setBroker(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEYS.ACCOUNT_ID);
      localStorage.removeItem(STORAGE_KEYS.TOKEN);
      localStorage.removeItem(STORAGE_KEYS.WEBHOOK_URL);
      localStorage.removeItem(STORAGE_KEYS.USER);
      localStorage.removeItem(STORAGE_KEYS.ENVIRONMENT);
    }
  }, []);

  const isAuthenticated = Boolean(user || accountId.trim());

  return {
    user,
    accountId,
    broker,
    token,
    webhookUrl,
    environment,
    isAuthenticated,
    isLoading,
    setAccountId,
    setToken,
    setWebhookUrl,
    setEnvironment,
    logout,
  };
}
