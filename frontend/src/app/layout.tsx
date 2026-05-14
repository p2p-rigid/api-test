import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "User Query Chat",
  description: "Natural language interface for querying users",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
