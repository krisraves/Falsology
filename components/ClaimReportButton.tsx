"use client";

import { useState } from "react";
import { ReportDialog } from "@/components/ReportDialog";

export function ClaimReportButton({ claimId }: { claimId: string }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="button button-outline button-small" onClick={() => setOpen(true)}>⚑ Report an issue</button>
      {open ? <ReportDialog claimId={claimId} onClose={() => setOpen(false)} /> : null}
    </>
  );
}
