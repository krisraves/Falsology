import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Falsology",
    short_name: "Falsology",
    description: "Watch a claim, decide Truth or Lie, then inspect the evidence.",
    start_url: "/play",
    display: "standalone",
    background_color: "#f3f0e9",
    theme_color: "#0b0d0f",
    icons: [{ src: "/icon", sizes: "512x512", type: "image/png" }],
  };
}
