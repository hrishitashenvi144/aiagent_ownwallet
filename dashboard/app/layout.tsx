import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "AuditAgent | Pre-Audit Smart Contract Security Triage",
  description: "Autonomous AI smart contract security auditor micro-business on Base Sepolia.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans">
        <Providers>
          <Header />
          <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}