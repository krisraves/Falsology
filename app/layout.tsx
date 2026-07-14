import type { Metadata, Viewport } from "next";
import "@/app/globals.css";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { SITE_DESCRIPTION, SITE_NAME, siteUrl } from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: { default: `${SITE_NAME} — Truth, lie, or something in between?`, template: `%s | ${SITE_NAME}` },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  keywords: ["truth or lie", "fact checking game", "media literacy", "historical lies", "evidence"],
  openGraph: {
    title: `${SITE_NAME} — Watch. Decide. Verify.`,
    description: SITE_DESCRIPTION,
    type: "website",
    url: siteUrl(),
    siteName: SITE_NAME,
  },
  twitter: { card: "summary_large_image", title: SITE_NAME, description: SITE_DESCRIPTION },
  alternates: { canonical: siteUrl() },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0b0d0f",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">Skip to content</a>
        <Header />
        <div id="main-content">{children}</div>
        <Footer />
      </body>
    </html>
  );
}
