import { ImageResponse } from "next/og";

export const alt = "Falsology — Watch. Decide. Verify.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", background: "#0b0d0f", color: "#f7f4ee", padding: 72, fontFamily: "sans-serif" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 22, fontSize: 42, fontWeight: 800 }}>
        <div style={{ width: 72, height: 72, background: "#f4ff63", color: "#0b0d0f", display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 18 }}>F</div>
        FALSOLOGY
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ color: "#f4ff63", fontSize: 26, letterSpacing: 6, fontWeight: 700 }}>WATCH · DECIDE · VERIFY</div>
        <div style={{ fontSize: 82, lineHeight: 1.02, fontWeight: 900, maxWidth: 1000 }}>People sound certain. The record is less polite.</div>
      </div>
      <div style={{ display: "flex", gap: 18, fontSize: 26 }}>
        <span style={{ padding: "14px 24px", border: "2px solid #f7f4ee", borderRadius: 999 }}>TRUTH</span>
        <span style={{ padding: "14px 24px", background: "#f7f4ee", color: "#0b0d0f", borderRadius: 999 }}>LIE</span>
      </div>
    </div>,
    size,
  );
}
