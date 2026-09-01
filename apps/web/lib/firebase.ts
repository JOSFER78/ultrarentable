/**
 * apps/web/lib/firebase.ts
 * Reescrito 2026-09-01 (AG-11 T4 + corrección del orquestador — W5.6).
 *
 * ANTES: mezclaba DOS proyectos de Firebase distintos vía fallbacks hardcodeados —
 * apiKey/authDomain/projectId/storageBucket de "goalskid-app" con databaseURL de "pecemi".
 * Esos fallbacks eran los que se usaban de verdad (no existía apps/web/.env.local), y son la
 * causa raíz medida del watchdog de 6s en el login.
 *
 * AHORA: la configuración sale EXCLUSIVAMENTE de las 7 variables NEXT_PUBLIC_FIREBASE_*.
 * Si falta una, se lanza un error explícito y legible. NUNCA se rellena con un valor por
 * defecto: arrancar en silencio contra el proyecto equivocado es justamente la mentira que se
 * retira aquí (doctrina REAL-ONLY: sin dato ⇒ ERROR, jamás un valor inventado).
 *
 * POR QUÉ LA INICIALIZACIÓN ES PEREZOSA (corrección del orquestador):
 * la primera versión llamaba a readEnvOrFail() en el ámbito del módulo. Como AuthContext.tsx
 * importa este fichero y envuelve toda la app, `next build` reventaba al prerenderizar
 * CUALQUIER página mientras no existiese .env.local — es decir, el build entero pasaba a
 * depender de que Emilio pegase las claves. Se difiere la comprobación al primer USO real de
 * Firebase mediante Proxy: no se falsea nada, el error sigue siendo ruidoso e inmediato en
 * cuanto algo toca auth/rtdb, pero las páginas que no usan autenticación compilan y se sirven.
 */
import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, Auth } from "firebase/auth";
import { getDatabase, Database } from "firebase/database";

const REQUIRED_ENV_VARS = [
  "NEXT_PUBLIC_FIREBASE_API_KEY",
  "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN",
  "NEXT_PUBLIC_FIREBASE_DATABASE_URL",
  "NEXT_PUBLIC_FIREBASE_PROJECT_ID",
  "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET",
  "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID",
  "NEXT_PUBLIC_FIREBASE_APP_ID",
] as const;

type RequiredEnvVar = (typeof REQUIRED_ENV_VARS)[number];

/**
 * Next.js sustituye `process.env.NEXT_PUBLIC_*` en tiempo de compilación por su literal, así
 * que hay que nombrarlas una a una: un acceso dinámico `process.env[name]` NO se sustituye y
 * saldría siempre undefined en el cliente.
 */
const ENV_VALUES: Record<RequiredEnvVar, string | undefined> = {
  NEXT_PUBLIC_FIREBASE_API_KEY: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  NEXT_PUBLIC_FIREBASE_DATABASE_URL: process.env.NEXT_PUBLIC_FIREBASE_DATABASE_URL,
  NEXT_PUBLIC_FIREBASE_PROJECT_ID: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  NEXT_PUBLIC_FIREBASE_APP_ID: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

/** Lista de variables ausentes. Vacía = configuración completa. */
export function missingFirebaseEnvVars(): RequiredEnvVar[] {
  return REQUIRED_ENV_VARS.filter((name) => {
    const value = ENV_VALUES[name];
    return !value || !value.trim();
  });
}

/** `true` si Firebase está configurado. Permite a la UI avisar en gris en vez de reventar. */
export function isFirebaseConfigured(): boolean {
  return missingFirebaseEnvVars().length === 0;
}

function buildConfig() {
  const missing = missingFirebaseEnvVars();
  if (missing.length > 0) {
    throw new Error(
      `[firebase.ts] Configuración de Firebase incompleta. Faltan: ${missing.join(", ")}. ` +
        `Copia apps/web/.env.local.example a apps/web/.env.local y pega las 7 claves ` +
        `(consola de Firebase → Configuración del proyecto → Tus apps → SDK). ` +
        `No hay valor por defecto a propósito: arrancar contra el proyecto equivocado en ` +
        `silencio es el fallo que causaba el watchdog de 6s en el login.`
    );
  }
  return {
    apiKey: ENV_VALUES.NEXT_PUBLIC_FIREBASE_API_KEY as string,
    authDomain: ENV_VALUES.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN as string,
    databaseURL: ENV_VALUES.NEXT_PUBLIC_FIREBASE_DATABASE_URL as string,
    projectId: ENV_VALUES.NEXT_PUBLIC_FIREBASE_PROJECT_ID as string,
    storageBucket: ENV_VALUES.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET as string,
    messagingSenderId: ENV_VALUES.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID as string,
    appId: ENV_VALUES.NEXT_PUBLIC_FIREBASE_APP_ID as string,
  };
}

let _app: FirebaseApp | null = null;
let _auth: Auth | null = null;
let _rtdb: Database | null = null;
let _provider: GoogleAuthProvider | null = null;

export function getFirebaseApp(): FirebaseApp {
  if (!_app) {
    _app = getApps().length > 0 ? getApp() : initializeApp(buildConfig());
  }
  return _app;
}

export function getFirebaseAuth(): Auth {
  if (!_auth) _auth = getAuth(getFirebaseApp());
  return _auth;
}

export function getFirebaseRtdb(): Database {
  if (!_rtdb) _rtdb = getDatabase(getFirebaseApp());
  return _rtdb;
}

export function getGoogleProvider(): GoogleAuthProvider {
  if (!_provider) {
    _provider = new GoogleAuthProvider();
    _provider.setCustomParameters({ prompt: "select_account" });
  }
  return _provider;
}

/**
 * Proxies perezosos: conservan la superficie de importación previa (`auth`, `rtdb`,
 * `googleProvider`) para no tocar AuthContext, pero no inicializan nada hasta que alguien
 * accede de verdad a una propiedad. Si falta configuración, el error salta AHÍ, con su
 * mensaje completo — no al importar el módulo.
 */
function lazyProxy<T extends object>(resolve: () => T): T {
  return new Proxy({} as T, {
    get(_target, prop, receiver) {
      const value = Reflect.get(resolve() as object, prop, receiver);
      return typeof value === "function" ? value.bind(resolve()) : value;
    },
    set(_target, prop, value) {
      return Reflect.set(resolve() as object, prop, value);
    },
    has(_target, prop) {
      return Reflect.has(resolve() as object, prop);
    },
  });
}

export const auth: Auth = lazyProxy<Auth>(getFirebaseAuth);
export const rtdb: Database = lazyProxy<Database>(getFirebaseRtdb);
export const googleProvider: GoogleAuthProvider = lazyProxy<GoogleAuthProvider>(getGoogleProvider);

export default getFirebaseApp;
