import type { Metadata, Viewport } from "next";
import Script from "next/script";
import "@/app/globals.css";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { SITE_NAME, siteUrl } from "@/lib/site";

const description = "Train your discernment on real spoken statements from suspects, criminals, witnesses, survivors, and public figures. Watch the clip, make the call, then inspect the evidence.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: { default: `${SITE_NAME} — Can you read the case?`, template: `%s | ${SITE_NAME}` },
  description,
  applicationName: SITE_NAME,
  keywords: ["detective game", "truth or lie", "deception detection", "media literacy", "criminal interviews", "evidence training"],
  openGraph: { title: `${SITE_NAME} — Evidence beats instinct`, description, type: "website", url: siteUrl(), siteName: SITE_NAME },
  twitter: { card: "summary_large_image", title: SITE_NAME, description },
  alternates: { canonical: siteUrl() },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#080b10",
  colorScheme: "dark",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const adsClient = process.env.NEXT_PUBLIC_GOOGLE_ADSENSE_CLIENT;
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Header />
        <div id="main-content">{children}</div>
        <Footer />
        {adsClient ? (
          <Script
            id="adsense-loader"
            async
            strategy="afterInteractive"
            crossOrigin="anonymous"
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${adsClient}`}
          />
        ) : null}
      </body>
    </html>
  );
}
