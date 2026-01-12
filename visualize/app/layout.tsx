import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/Navigation";
import { Footer } from "@/components/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'https://taskpedia.ai'),
  title: {
    default: "TASKPEDIA - Hierarchical Task Decomposition Dataset for Embodied AI",
    template: "%s | TASKPEDIA"
  },
  description: "Explore millions of atomic robot-executable actions decomposed from human activities. A comprehensive hierarchical task dataset for VLA/VLN training with 3,479+ atomic verbs across 35+ domains.",
  keywords: [
    "embodied AI",
    "task decomposition",
    "robot actions",
    "VLA training",
    "VLN dataset",
    "atomic actions",
    "hierarchical tasks",
    "robot learning",
    "O*NET taxonomy",
    "task planning",
    "manipulation tasks",
    "robot primitives"
  ],
  authors: [{ name: "Sentient-x" }],
  creator: "Sentient-x",
  publisher: "TASKPEDIA",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    title: "TASKPEDIA - Hierarchical Task Decomposition Dataset",
    description: "Millions of atomic robot-executable actions for embodied AI training",
    siteName: "TASKPEDIA",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "TASKPEDIA - Task Decomposition for Embodied AI",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "TASKPEDIA - Hierarchical Task Decomposition Dataset",
    description: "Millions of atomic robot-executable actions for embodied AI training",
    creator: "@sentientx",
    images: ["/og-image.png"],
  },
  alternates: {
    canonical: "/",
  },
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
        <link rel="manifest" href="/site.webmanifest" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Dataset",
              "name": "TASKPEDIA",
              "description": "Hierarchical task decomposition dataset containing millions of atomic robot-executable actions for embodied AI training",
              "url": process.env.NEXT_PUBLIC_BASE_URL || 'https://taskpedia.ai',
              "keywords": "embodied AI, task decomposition, robot actions, VLA training, atomic verbs",
              "creator": {
                "@type": "Organization",
                "name": "Sentient-x"
              },
              "distribution": {
                "@type": "DataDownload",
                "encodingFormat": "application/json",
                "contentUrl": "https://huggingface.co/datasets/Sentient-x/taskpedia"
              },
              "temporalCoverage": "2024/..",
              "license": "https://creativecommons.org/licenses/by/4.0/"
            })
          }}
        />
      </head>
      <body className={`${inter.className} antialiased bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 min-h-screen`}>
        <Navigation />
        <main className="min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
