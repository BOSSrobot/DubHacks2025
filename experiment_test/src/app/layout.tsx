import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { StatsigBootstrapProvider } from "@statsig/next";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const user = {
    userID: `user-${Math.random().toString(36).substring(2, 15)}`,
  };

  return (
    <html lang="en">
      <body
        className={`antialiased`}
      >
        <StatsigBootstrapProvider
          user={user}
          clientKey={process.env.NEXT_PUBLIC_STATSIG_CLIENT_KEY!}
          serverKey={process.env.STATSIG_SERVER_KEY!}
        >
          {children}
        </StatsigBootstrapProvider>
      </body>
    </html>
  );
}