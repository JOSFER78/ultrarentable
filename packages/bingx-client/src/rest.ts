import crypto from "crypto";

export interface BingXConfig {
  apiKey?: string;
  secretKey?: string;
  baseUrl?: string;
  fallbackUrl?: string;
  recvWindow?: number;
  timeOffsetMs?: number;
  timeoutMs?: number;
}

type ParamValue = string | number | boolean;
type Params = Record<string, ParamValue>;

export class BingXRestClient {
  private readonly apiKey: string;
  private readonly secretKey: string;
  private readonly baseUrls: string[];
  private readonly recvWindow: number;
  private readonly timeoutMs: number;
  private timeOffsetMs: number;

  constructor(config: BingXConfig = {}) {
    this.apiKey = config.apiKey || process.env.BINGX_API_KEY || "";
    this.secretKey = config.secretKey || process.env.BINGX_SECRET_KEY || "";
    this.baseUrls = [
      config.baseUrl || process.env.BINGX_BASE_URL || "https://open-api.bingx.com",
      config.fallbackUrl || process.env.BINGX_FALLBACK_URL || "https://open-api.bingx.pro",
    ].filter((value, index, all) => all.indexOf(value) === index);
    this.recvWindow = config.recvWindow ?? Number(process.env.BINGX_RECV_WINDOW || 5000);
    this.timeOffsetMs = config.timeOffsetMs ?? 0;
    this.timeoutMs = config.timeoutMs ?? 10000;
  }

  public setTimeOffsetMs(offset: number): void {
    if (!Number.isFinite(offset)) throw new Error("INVALID_TIME_OFFSET");
    this.timeOffsetMs = Math.trunc(offset);
  }

  private validateParams(params: Params): void {
    const forbidden = /[&=?#\r\n]/;
    for (const [key, value] of Object.entries(params)) {
      if (forbidden.test(String(key)) || forbidden.test(String(value))) {
        throw new Error(`INVALID_PARAMETER_CHARACTERS: ${key}`);
      }
    }
  }

  private canonicalQuery(params: Params): string {
    this.validateParams(params);
    return Object.keys(params)
      .sort()
      .map((key) => `${key}=${params[key]}`)
      .join("&");
  }

  private signature(query: string): string {
    return crypto.createHmac("sha256", this.secretKey).update(query).digest("hex");
  }

  private isNetworkOrTimeout(error: unknown): boolean {
    return (
      error instanceof TypeError ||
      (error instanceof DOMException && (error.name === "AbortError" || error.name === "TimeoutError")) ||
      (error instanceof Error && (error.name === "AbortError" || error.name === "TimeoutError"))
    );
  }

  private async requestJson<T>(url: string, headers: Record<string, string>): Promise<T> {
    const response = await fetch(url, {
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(this.timeoutMs),
    });
    const text = await response.text();
    let payload: any;
    try {
      payload = JSON.parse(text);
    } catch {
      throw new Error(`BINGX_INVALID_JSON: HTTP ${response.status}`);
    }
    if (!response.ok) throw new Error(`BINGX_HTTP_ERROR: ${response.status}`);
    if (payload?.code !== 0) {
      throw new Error(`BINGX_API_ERROR [${payload?.code}]: ${payload?.msg || "Unknown error"}`);
    }
    return payload.data as T;
  }

  public async publicGet<T = unknown>(endpoint: string, params: Params = {}): Promise<T> {
    const query = this.canonicalQuery(params);
    let lastError: unknown;
    for (const base of this.baseUrls) {
      try {
        const url = `${base}${endpoint}${query ? `?${query}` : ""}`;
        return await this.requestJson<T>(url, {
          Accept: "application/json",
          "X-SOURCE-KEY": "BX-AI-SKILL",
        });
      } catch (error) {
        lastError = error;
        if (!this.isNetworkOrTimeout(error)) throw error;
      }
    }
    throw lastError instanceof Error ? lastError : new Error(String(lastError));
  }

  public async signedGet<T = unknown>(endpoint: string, params: Params = {}): Promise<T> {
    if (!this.apiKey || !this.secretKey) {
      throw new Error("AUTHENTICATION_FAILED: Missing BINGX_API_KEY or BINGX_SECRET_KEY");
    }
    const all: Params = {
      ...params,
      recvWindow: this.recvWindow,
      timestamp: Date.now() + this.timeOffsetMs,
    };
    const query = this.canonicalQuery(all);
    const signed = `${query}&signature=${this.signature(query)}`;
    let lastError: unknown;
    for (const base of this.baseUrls) {
      try {
        return await this.requestJson<T>(`${base}${endpoint}?${signed}`, {
          Accept: "application/json",
          "X-BX-APIKEY": this.apiKey,
          "X-SOURCE-KEY": "BX-AI-SKILL",
        });
      } catch (error) {
        lastError = error;
        if (!this.isNetworkOrTimeout(error)) throw error;
      }
    }
    throw lastError instanceof Error ? lastError : new Error(String(lastError));
  }

  public getContracts() {
    return this.publicGet<any[]>("/openApi/swap/v2/quote/contracts");
  }

  public getKlines(
    symbol: string,
    interval: string,
    limit = 1000,
    startTime?: number,
    endTime?: number,
  ) {
    const params: Params = { symbol, interval, limit };
    if (startTime !== undefined) params.startTime = startTime;
    if (endTime !== undefined) params.endTime = endTime;
    return this.publicGet<any[]>("/openApi/swap/v3/quote/klines", params);
  }

  public getPremiumIndex(symbol?: string) {
    return this.publicGet<any>(
      "/openApi/swap/v2/quote/premiumIndex",
      symbol ? { symbol } : {},
    );
  }

  public getDepth(symbol: string, limit = 20) {
    return this.publicGet<any>("/openApi/swap/v2/quote/depth", { symbol, limit });
  }

  public getRecentTrades(symbol: string, limit = 100) {
    return this.publicGet<any[]>("/openApi/swap/v2/quote/trades", { symbol, limit });
  }

  public getTicker(symbol?: string) {
    return this.publicGet<any>(
      "/openApi/swap/v2/quote/ticker",
      symbol ? { symbol } : {},
    );
  }

  public getAccountBalance() {
    return this.signedGet<any>("/openApi/swap/v3/user/balance");
  }

  public getPositions(symbol?: string) {
    return this.signedGet<any[]>(
      "/openApi/swap/v2/user/positions",
      symbol ? { symbol } : {},
    );
  }

  public getCommissionRate(symbol?: string) {
    return this.signedGet<any>(
      "/openApi/swap/v2/user/commissionRate",
      symbol ? { symbol } : {},
    );
  }
}
