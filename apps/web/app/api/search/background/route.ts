import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-static";

/**
 * API route Next.ts que proxea /api/search/background -> FastAPI :8000.
 * Estrategia same-origin ya usada en la app: el navegador habla con :3000 y Next
 * reenvía a la API local, evitando CORS y bloqueos de puerto.
 */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function GET(request: NextRequest) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/search/background`, {
      cache: "no-store",
      signal: AbortSignal.timeout(6000),
    });
    if (!res.ok) {
      return NextResponse.json(
        { status: "ERROR", detail: `API_HTTP_${res.status}` },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json(
      { status: "ERROR", detail: err?.message || "SERVICE_UNAVAILABLE" },
      { status: 502 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/search/background/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      cache: "no-store",
      signal: AbortSignal.timeout(6000),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json(
      { status: "ERROR", detail: err?.message || "SERVICE_UNAVAILABLE" },
      { status: 502 }
    );
  }
}
