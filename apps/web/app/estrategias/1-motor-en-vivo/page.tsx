"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function RedirectToEstrategias() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/estrategias");
  }, [router]);
  return null;
}