/**
 * apps/web/app/api/local/superadmin/route.ts
 *
 * Sesión permanente del superadministrador en la instancia LOCAL (puerto 3100).
 * Mandato explícito de Emilio: el superadmin único registrado en Firebase.
 */

import { NextResponse } from "next/server";
import { headers } from "next/headers";

export const dynamic = "force-dynamic";

/** Correo del superadministrador registrado en Firebase. El original vive en AuthContext.tsx y deben coincidir. */
export const SUPERADMIN_EMAIL = "josferestudio@gmail.com";

function esHostLocal(host: string | null): boolean {
  if (!host) return false;
  let sinPuerto = host.toLowerCase().trim();
  if (sinPuerto.startsWith("[")) {
    const cierre = sinPuerto.indexOf("]");
    if (cierre !== -1) {
      sinPuerto = sinPuerto.slice(0, cierre + 1);
    }
  } else {
    sinPuerto = sinPuerto.split(":")[0].trim();
  }
  return (
    sinPuerto === "localhost" ||
    sinPuerto === "127.0.0.1" ||
    sinPuerto === "::1" ||
    sinPuerto === "[::1]"
  );
}

export async function GET() {
  const variableActiva = process.env.ULTRARENTABLE_LOCAL_SUPERADMIN === "1";
  if (!variableActiva) {
    return NextResponse.json({
      enabled: false,
      motivo: "la variable de entorno ULTRARENTABLE_LOCAL_SUPERADMIN no está activa (valor esperado: '1')",
    });
  }

  const cabeceras = headers();
  const host = cabeceras.get("host");
  const local = esHostLocal(host);

  if (!local) {
    return NextResponse.json({
      enabled: false,
      motivo: `el host de la peticion (${host}) no es local`,
    });
  }

  const res = NextResponse.json({
    enabled: true,
    email: SUPERADMIN_EMAIL,
    // UID real de Firebase Authentication asignado a josferestudio@gmail.com (José Fernández)
    // para coherencia con las reglas de RTDB y perfil de usuario local.
    uid: "dIJLLgptqmelX0oA2GkUq7RtqG53",
    displayName: "José Fernández",
    role: "superadmin",
    status: "AUTHORIZED",
    is_superadmin: true,
    is_authorized: true,
    host,
  });

  // Sellado de cookie persistente por 1 año
  // httpOnly: false porque el cliente en AuthContext.tsx verifica document.cookie.includes("ultra_local_admin")
  res.cookies.set("ultra_local_admin", SUPERADMIN_EMAIL, {
    path: "/",
    maxAge: 31536000,
    sameSite: "lax",
    httpOnly: false,
  });

  return res;
}
