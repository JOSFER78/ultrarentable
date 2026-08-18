import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = "http://127.0.0.1:8000";

export async function GET(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  const path = resolvedParams.path.join("/");
  const search = req.nextUrl.search;
  const targetUrl = `${BACKEND_URL}/api/v1/${path}${search}`;

  try {
    const res = await fetch(targetUrl, {
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json({ error: "Backend proxy error", details: err?.message }, { status: 502 });
  }
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const resolvedParams = await params;
  const path = resolvedParams.path.join("/");
  const search = req.nextUrl.search;
  const targetUrl = `${BACKEND_URL}/api/v1/${path}${search}`;

  try {
    const body = await req.json().catch(() => null);
    const res = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json({ error: "Backend proxy error", details: err?.message }, { status: 502 });
  }
}
