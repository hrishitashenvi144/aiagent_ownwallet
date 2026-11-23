"use client";

import React from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  // In full implementation, wraps wagmi/viem QueryClientProvider & WagmiProvider
  return <>{children}</>;
}