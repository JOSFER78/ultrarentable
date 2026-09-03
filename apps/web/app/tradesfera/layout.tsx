import React from "react";

export default function TradesferaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="w-full space-y-3 pb-8 text-[var(--text-1)]">
      {children}
    </div>
  );
}
