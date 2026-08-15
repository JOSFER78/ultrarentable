"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  CandlestickSeries,
  AreaSeries,
  createSeriesMarkers,
  type IChartApi,
  type UTCTimestamp,
  ColorType,
  CrosshairMode,
} from "lightweight-charts";

export interface CandleData {
  time: number | string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MarkerData {
  time: number | string;
  position: "aboveBar" | "belowBar";
  color: string;
  shape: "arrowUp" | "arrowDown" | "circle";
  text: string;
}

export interface EquityPoint {
  time: number | string;
  value: number;
}

interface ChartProps {
  candles?: CandleData[];
  equity?: EquityPoint[];
  markers?: MarkerData[];
  height?: number;
  mode?: "candles" | "equity";
}

export default function Chart({
  candles = [],
  equity = [],
  markers = [],
  height = 400,
  mode = "candles",
}: ChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        fontFamily: "'Inter', sans-serif",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(148, 163, 184, 0.06)" },
        horzLines: { color: "rgba(148, 163, 184, 0.06)" },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: {
        borderColor: "rgba(148, 163, 184, 0.12)",
      },
      timeScale: {
        borderColor: "rgba(148, 163, 184, 0.12)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    try {
      if (mode === "candles" && candles.length > 0) {
        const series = chart.addSeries(CandlestickSeries, {
          upColor: "#22c55e",
          downColor: "#ef4444",
          borderUpColor: "#22c55e",
          borderDownColor: "#ef4444",
          wickUpColor: "#22c55e",
          wickDownColor: "#ef4444",
        });
        series.setData(candles as any);

        if (markers.length > 0) {
          createSeriesMarkers(series as any, markers as any);
        }
      }

      if (mode === "equity" && equity.length > 0) {
        const series = chart.addSeries(AreaSeries, {
          lineColor: "#63e1b4",
          topColor: "rgba(99, 225, 180, 0.25)",
          bottomColor: "rgba(99, 225, 180, 0.02)",
          lineWidth: 2,
        });
        series.setData(equity as any);
      }

      chart.timeScale().fitContent();
    } catch (err) {
      console.error("Lightweight charts render error:", err);
    }

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [candles, equity, markers, height, mode]);

  return (
    <div
      ref={containerRef}
      style={{
        width: "100%",
        height,
        borderRadius: "var(--radius-md)",
        overflow: "hidden",
      }}
    />
  );
}
