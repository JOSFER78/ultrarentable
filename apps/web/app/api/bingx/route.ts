import { NextResponse } from "next/server";

export const dynamic = "force-static";

const BINGX_BASE = process.env.BINGX_BASE_URL || "https://open-api.bingx.com";

const ALLOWED = new Set([
  "/openApi/swap/v2/quote/contracts",
  "/openApi/swap/v3/quote/klines",
  "/openApi/swap/v2/quote/premiumIndex",
  "/openApi/swap/v2/quote/fundingRate",
  "/openApi/swap/v2/quote/depth",
  "/openApi/swap/v2/quote/trades",
  "/openApi/swap/v2/quote/ticker",
]);

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get("endpoint");

  if (!endpoint || !ALLOWED.has(endpoint)) {
    return NextResponse.json({ error: "Endpoint not allowed" }, { status: 403 });
  }

  const forwardParams = new URLSearchParams();
  searchParams.forEach((value, key) => {
    if (key !== "endpoint") forwardParams.set(key, value);
  });

  const url = `${BINGX_BASE}${endpoint}${forwardParams.size ? `?${forwardParams}` : ""}`;

  try {
    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "X-SOURCE-KEY": "BX-AI-SKILL",
      },
      signal: AbortSignal.timeout(8000),
    });
    const text = await response.text();
    let payload: unknown;
    try {
      payload = JSON.parse(text);
    } catch {
      return NextResponse.json({ error: "Invalid JSON from BingX" }, { status: 502 });
    }
    return NextResponse.json(payload, { status: response.ok ? 200 : response.status });
  } catch (error) {
    return NextResponse.json(
      { error: "BingX API error", detail: String(error) },
      { status: 502 },
    );
  }
}
