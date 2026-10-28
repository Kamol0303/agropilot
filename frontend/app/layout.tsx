import type { ReactNode } from "react";

export const metadata = {
  title: "AgroPilot",
  description: "NASA ma'lumotlari asosidagi fermerlar uchun platforma",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uz">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: "#f6f8f4", color: "#1d2b1f" }}>
        <header style={{ padding: "16px 24px", background: "#2f6b3a", color: "#fff", fontWeight: 600 }}>
          🌾 AgroPilot
        </header>
        <main style={{ maxWidth: 960, margin: "0 auto", padding: 24 }}>{children}</main>
      </body>
    </html>
  );
}
