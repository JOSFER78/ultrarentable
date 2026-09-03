import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 90;

const BACKEND_INTERNAL_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8100";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { message, history = [] } = body;

    if (!message || typeof message !== "string") {
      return NextResponse.json({ error: "Message is required" }, { status: 400 });
    }

    const backendRes = await fetch(`${BACKEND_INTERNAL_URL}/api/v1/providers/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ message, history }),
    });

    if (!backendRes.ok) {
      const errText = await backendRes.text();
      console.error(`[AI Chat] Error desde backend (${backendRes.status}):`, errText);
      return NextResponse.json(
        {
          response:
            "⚠️ Ocurrió una pausa temporal en el servicio de IA del backend. Por favor intenta de nuevo.",
          error: `HTTP ${backendRes.status}: ${errText}`,
        },
        { status: backendRes.status }
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error("Error in prop-firms chat route:", error);
    return NextResponse.json(
      {
        response:
          "⚠️ Ocurrió una pausa temporal en el servicio de IA. Por favor intenta de nuevo.",
        error: error.message,
      },
      { status: 500 }
    );
  }
}
