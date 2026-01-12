import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/Navigation";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_BASE_URL || "https://taskpedia.ai",
  ),
  title: {
    default: "TASKPEDIA - Hierarchical Task Decomposition for Embodied AI",
    template: "%s | TASKPEDIA",
  },
  description:
    "Explore millions of atomic robot-executable actions. A comprehensive hierarchical task dataset for VLA/VLN training.",
  keywords: [
    "embodied AI",
    "task decomposition",
    "robot actions",
    "VLA training",
    "atomic actions",
  ],
  openGraph: {
    type: "website",
    locale: "en_US",
    title: "TASKPEDIA - Task Decomposition for Embodied AI",
    description:
      "Millions of atomic robot-executable actions for embodied AI training",
    siteName: "TASKPEDIA",
  },
  twitter: {
    card: "summary_large_image",
    title: "TASKPEDIA - Hierarchical Task Decomposition",
    description:
      "Millions of atomic robot-executable actions for embodied AI training",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Dataset",
              name: "TASKPEDIA",
              description:
                "Hierarchical task decomposition dataset for embodied AI training",
              creator: { "@type": "Organization", name: "Sentient-x" },
              license: "https://creativecommons.org/licenses/by/4.0/",
            }),
          }}
        />
      </head>
      <body
        className={`${inter.variable} ${jetbrains.variable} font-sans min-h-screen bg-[#030014] noise`}
      >
        {/* Background effects */}
        <div className="fixed inset-0 bg-grid pointer-events-none" />
        <div className="fixed top-0 left-1/4 w-[600px] h-[600px] bg-violet-600/20 rounded-full blur-[150px] pointer-events-none" />
        <div className="fixed bottom-0 right-1/4 w-[500px] h-[500px] bg-fuchsia-600/15 rounded-full blur-[150px] pointer-events-none" />
        <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-purple-600/10 rounded-full blur-[200px] pointer-events-none animate-pulse-glow" />

        <Navigation />
        <main className="relative z-10">{children}</main>
      </body>
    </html>
  );
}
