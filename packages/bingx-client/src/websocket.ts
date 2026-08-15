import { EventEmitter } from "events";
import WebSocket from "ws";
import zlib from "zlib";

export interface MarketEvent {
  feedType: "trade" | "depth" | "mark_price" | "kline" | "unknown";
  symbol: string;
  exchangeTimestamp: number | null;
  receiveTimestamp: number;
  dataType: string;
  data: unknown;
}

type Subscription = { dataType: string; id: string };

export class BingXWebSocketClient extends EventEmitter {
  private readonly wsUrl: string;
  private ws: WebSocket | null = null;
  private subscriptions = new Map<string, Subscription>();
  private reconnectAttempt = 0;
  private closedByUser = false;
  private reconnectTimer: NodeJS.Timeout | null = null;

  constructor(wsUrl = "wss://open-api-swap.bingx.com/swap-market") {
    super();
    this.wsUrl = wsUrl;
  }

  public async connect(): Promise<void> {
    this.closedByUser = false;
    await new Promise<void>((resolve, reject) => {
      const socket = new WebSocket(this.wsUrl);
      this.ws = socket;
      const timeout = setTimeout(() => {
        socket.terminate();
        reject(new Error("WEBSOCKET_CONNECT_TIMEOUT"));
      }, 10000);

      socket.once("open", () => {
        clearTimeout(timeout);
        this.reconnectAttempt = 0;
        this.emit("connected");
        for (const subscription of this.subscriptions.values()) {
          this.sendSubscription(subscription);
        }
        resolve();
      });

      socket.on("message", (buffer) => this.handleMessage(buffer, Date.now()));
      socket.on("error", (error) => this.emit("error", error));
      socket.on("close", (code, reason) => {
        clearTimeout(timeout);
        this.emit("disconnected", { code, reason: reason.toString() });
        if (!this.closedByUser) this.scheduleReconnect();
      });
    });
  }

  private decode(buffer: WebSocket.RawData): string {
    if (Buffer.isBuffer(buffer)) {
      try {
        return zlib.gunzipSync(buffer).toString("utf8");
      } catch {
        return buffer.toString("utf8");
      }
    }
    if (Array.isArray(buffer)) return Buffer.concat(buffer).toString("utf8");
    return Buffer.from(buffer as ArrayBuffer).toString("utf8");
  }

  private handleMessage(buffer: WebSocket.RawData, receiveTimestamp: number): void {
    try {
      const text = this.decode(buffer).trim();
      if (text === "Ping") {
        this.ws?.send("Pong");
        return;
      }
      if (text === "Pong") return;

      let message: any;
      try {
        message = JSON.parse(text);
      } catch {
        this.emit("unparsedMessage", { text, receiveTimestamp });
        return;
      }

      if (message?.ping !== undefined) {
        this.ws?.send(JSON.stringify({ pong: message.ping }));
        return;
      }

      if (!message?.dataType) {
        this.emit("controlMessage", message);
        return;
      }

      const dataType = String(message.dataType);
      const symbol = dataType.split("@")[0].toUpperCase();
      let feedType: MarketEvent["feedType"] = "unknown";
      if (dataType.includes("@trade")) feedType = "trade";
      else if (dataType.includes("@depth")) feedType = "depth";
      else if (dataType.includes("@markPrice")) feedType = "mark_price";
      else if (dataType.includes("@kline")) feedType = "kline";

      const event: MarketEvent = {
        feedType,
        symbol,
        exchangeTimestamp:
          typeof message.eventTime === "number"
            ? message.eventTime
            : typeof message.time === "number"
              ? message.time
              : null,
        receiveTimestamp,
        dataType,
        data: message.data,
      };
      this.emit("marketEvent", event);
      this.emit(`${feedType}:${symbol}`, event);
    } catch (error) {
      this.emit("parseError", error);
    }
  }

  public subscribe(dataType: string, id = `sub_${Date.now()}`): void {
    const subscription = { dataType, id };
    this.subscriptions.set(dataType, subscription);
    if (this.ws?.readyState === WebSocket.OPEN) this.sendSubscription(subscription);
  }

  private sendSubscription(subscription: Subscription): void {
    this.ws?.send(JSON.stringify({
      id: subscription.id,
      reqType: "sub",
      dataType: subscription.dataType,
    }));
  }

  public subscribeSymbolFeeds(symbol: string): void {
    const normalized = symbol.toLowerCase();
    this.subscribe(`${normalized}@trade`);
    this.subscribe(`${normalized}@depth20`);
    this.subscribe(`${normalized}@markPrice`);
    this.subscribe(`${normalized}@kline_1m`);
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    const delay = Math.min(30000, 1000 * 2 ** this.reconnectAttempt++);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch((error) => {
        this.emit("reconnectError", error);
        this.scheduleReconnect();
      });
    }, delay);
  }

  public close(): void {
    this.closedByUser = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.ws?.close();
    this.ws = null;
  }
}
