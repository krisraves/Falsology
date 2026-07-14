export function AdSlot({ label = "Advertisement", compact = false }: { label?: string; compact?: boolean }) {
  return (
    <aside className={`ad-slot ${compact ? "ad-slot-compact" : ""}`} aria-label={label}>
      <span>{label}</span>
      <p>Reserved ad space</p>
    </aside>
  );
}
