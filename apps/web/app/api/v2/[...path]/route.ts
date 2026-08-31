import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-static";

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

async function proxyRequest(req: NextRequest, prefix: string, paramsPromise: any) {
  const resolvedParams = await paramsPromise;
  const path = Array.isArray(resolvedParams?.path) ? resolvedParams.path.join("/") : "";
  const search = req.nextUrl.search || "";
  const targetUrl = `${BACKEND_URL}/${prefix}/${path}${search}`;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (!["host", "connection", "content-length"].includes(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  const method = req.method;
  let body: BodyInit | null = null;
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    try {
      body = await req.arrayBuffer();
    } catch {
      body = null;
    }
  }

  try {
    const res = await fetch(targetUrl, {
      method,
      headers,
      body,
      cache: "no-store",
    });

    const contentType = res.headers.get("content-type") || "";
    const contentDisposition = res.headers.get("content-disposition");

    // If SSE streaming response, pipe the body directly
    if (contentType.includes("text/event-stream")) {
      return new Response(res.body, {
        status: res.status,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache, no-transform",
          "Connection": "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    // If JSON
    if (contentType.includes("application/json")) {
      const data = await res.json();
      return NextResponse.json(data, { status: res.status });
    }

    // Binary file download or attachment
    if (
      contentDisposition ||
      contentType.includes("spreadsheetml") ||
      contentType.includes("octet-stream") ||
      contentType.includes("excel") ||
      contentType.includes("zip")
    ) {
      const buffer = await res.arrayBuffer();
      const outHeaders: Record<string, string> = {
        "Content-Type": contentType || "application/octet-stream",
      };
      if (contentDisposition) {
        outHeaders["Content-Disposition"] = contentDisposition;
      }
      return new Response(buffer, {
        status: res.status,
        headers: outHeaders,
      });
    }

    // Text or CSV payload
    const textData = await res.text();
    const outHeaders: Record<string, string> = {
      "Content-Type": contentType || "text/plain",
    };
    if (contentDisposition) {
      outHeaders["Content-Disposition"] = contentDisposition;
    }
    return new Response(textData, {
      status: res.status,
      headers: outHeaders,
    });

  } catch (err: any) {
    return NextResponse.json(
      { error: "Backend proxy error", details: err?.message, target: targetUrl },
      { status: 502 }
    );
  }
}

export async function GET(req: NextRequest, context: { params: any }) {
  return proxyRequest(req, "api/v2", context.params);
}

export async function POST(req: NextRequest, context: { params: any }) {
  return proxyRequest(req, "api/v2", context.params);
}

export async function PUT(req: NextRequest, context: { params: any }) {
  return proxyRequest(req, "api/v2", context.params);
}

export async function PATCH(req: NextRequest, context: { params: any }) {
  return proxyRequest(req, "api/v2", context.params);
}

export async function DELETE(req: NextRequest, context: { params: any }) {
  return proxyRequest(req, "api/v2", context.params);
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept",
    },
  });
}
