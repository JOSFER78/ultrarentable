"use client";

import React from "react";
import QuantTooltip from "./QuantTooltip";

interface MetricWithTooltipProps {
  label: string;
  value: string | number;
  termKey?: string;
  customTooltip?: string;
  benchmark?: string;
  valueColor?: string;
  subValue?: string;
}

export default function MetricWithTooltip({
  label,
  value,
  termKey,
  customTooltip,
  benchmark,
  valueColor = "text-slate-100",
  subValue,
}: MetricWithTooltipProps) {
  return (
    <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 backdrop-blur-md hover:border-slate-700 transition flex flex-col justify-between">
      <div className="flex items-center justify-between gap-1 mb-1">
        <span className="text-xs font-medium text-slate-400 flex items-center gap-1">
          {label}
        </span>
        <QuantTooltip
          term={termKey || label}
          text={customTooltip}
          benchmark={benchmark}
          iconSize={13}
        />
      </div>
      <div>
        <span className={`text-xl font-bold font-mono tracking-tight ${valueColor}`}>
          {value}
        </span>
        {subValue && (
          <span className="text-[11px] text-slate-500 block mt-0.5">{subValue}</span>
        )}
      </div>
    </div>
  );
}