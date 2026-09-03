/**
 * apps/web/app/api/local/superadmin/route.ts
 *
 * Sesión permanente del superadministrador en la instancia LOCAL (la que Emilio abre en
 * http://localhost:3100). Sin esto hay que pasar por el login de Google en cada arranque, que en
 * la máquina de trabajo no aporta nada: quien tiene acceso al PC ya tiene acceso al repositorio,
 * a la base canónica y a las claves.
 *
 * Dos condiciones, las DOS obligatorias, y las dos se evalúan **en el servidor y en tiempo de
 * ejecución** (no se cocinan en el bundle, al contrario que las NEXT_PUBLIC_*):
 *
 *   1. La variable de entorno `ULTRARENTABLE_LOCAL_SUPERADMIN` vale "1" en el proceso que sirve la
 *      web. Está en `apps/web/.env.local` del PC, que no se versiona (`.gitignore`). El `.env.local`
 *      del VPS no la tiene, así que el MISMO build servido allí no activa nada.
 *   2. La petición llega a un host local (`localhost` o `127.0.0.1`). Si alguien abre la web por su
 *      dominio o su IP pública, esta ruta responde `enabled:false` aunque la variable existiera.
 *
 * Es decir: la sesión local vive en el PC de Emilio y en ningún otro sitio. El resto del mundo
 * sigue pasando por Firebase y por la autorización del superadministrador.
 */

import { NextResponse } from "next/server";
import { headers } from "next/headers";

export const dynamic = "force-dynamic";

/** Correo del superadministrador. Mismo valor que `SUPERADMIN_EMAIL` en context/AuthContext.tsx. */
const SUPERADMIN_EMAIL = "josferestudio@gmail.com";

function esHostLocal(host: string | null): boolean {
  if (!host) return false;
  const sinPuerto = host.split(":")[0].toLowerCase().trim();
  return sinPuerto === "localhost" || sinPuerto === "127.0.0.1" || sinPuerto === "::1" || sinPuerto === "[::1]";
}

export async function GET() {
  const cabeceras = headers();
  const host = cabeceras.get("host");
  const local = esHostLocal(host);
  const variableActiva = process.env.ULTRARENTABLE_LOCAL_SUPERADMIN === "1";

  if (!variableActiva || !local) {
    // Se dice POR QUÉ está desactivada: si Emilio la echa en falta en su localhost, el motivo se
    // ve de un vistazo en la respuesta en vez de tener que adivinarlo.
    return NextResponse.json({
      enabled: false,
      motivo: !variableActiva
        ? "ULTRARENTABLE_LOCAL_SUPERADMIN no vale 1 en el proceso que sirve la web"
        : `el host de la peticion (${host}) no es local`,
    });
  }

  return NextResponse.json({
    enabled: true,
    email: SUPERADMIN_EMAIL,
    uid: "local-superadmin",
    displayName: "Josfer (Super Admin · sesión local)",
    host,
  });
}
