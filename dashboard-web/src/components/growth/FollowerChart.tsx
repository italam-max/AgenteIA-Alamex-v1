"use client";

import { useMemo, useState } from "react";

import { formatDateTime } from "@/lib/format";
import type { GrowthSnapshot } from "@/lib/types";

const WIDTH = 640;
const HEIGHT = 220;
const PADDING = { top: 16, right: 16, bottom: 24, left: 36 };

function niceTicks(max: number): number[] {
  const step = Math.max(1, Math.ceil(max / 4 / 10) * 10);
  const ticks: number[] = [];
  for (let v = 0; v <= max; v += step) ticks.push(v);
  return ticks;
}

export function FollowerChart({ snapshots, target }: { snapshots: GrowthSnapshot[]; target: number }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [showTable, setShowTable] = useState(false);

  const plot = useMemo(() => {
    if (snapshots.length === 0) return null;

    const maxFollowers = Math.max(target, ...snapshots.map((s) => s.followers_count));
    const yMax = Math.ceil((maxFollowers * 1.1) / 10) * 10 || 10;
    const innerWidth = WIDTH - PADDING.left - PADDING.right;
    const innerHeight = HEIGHT - PADDING.top - PADDING.bottom;

    const xFor = (index: number) =>
      snapshots.length === 1 ? PADDING.left : PADDING.left + (index / (snapshots.length - 1)) * innerWidth;
    const yFor = (value: number) => PADDING.top + innerHeight - (value / yMax) * innerHeight;

    const points = snapshots.map((s, i) => ({ x: xFor(i), y: yFor(s.followers_count), snapshot: s }));
    const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
    const areaPath = `${linePath} L${points[points.length - 1].x.toFixed(1)},${(PADDING.top + innerHeight).toFixed(1)} L${points[0].x.toFixed(1)},${(PADDING.top + innerHeight).toFixed(1)} Z`;

    return { points, linePath, areaPath, yMax, targetY: yFor(target), innerWidth, innerHeight };
  }, [snapshots, target]);

  if (!plot) {
    return <p className="text-sm text-muted-foreground">Todavía no hay lecturas de seguidores.</p>;
  }

  const hovered = hoverIndex !== null ? plot.points[hoverIndex] : null;

  function handlePointerMove(e: React.PointerEvent<SVGSVGElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const relativeX = ((e.clientX - rect.left) / rect.width) * WIDTH;
    let nearest = 0;
    let nearestDistance = Infinity;
    plot!.points.forEach((p, i) => {
      const distance = Math.abs(p.x - relativeX);
      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearest = i;
      }
    });
    setHoverIndex(nearest);
  }

  const ticks = niceTicks(plot.yMax);

  return (
    <div className="space-y-2">
      <div className="relative">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          className="w-full touch-none"
          role="img"
          aria-label={`Seguidores a lo largo del tiempo, meta ${target}`}
          onPointerMove={handlePointerMove}
          onPointerLeave={() => setHoverIndex(null)}
        >
          {ticks.map((tick) => {
            const y = PADDING.top + plot.innerHeight - (tick / plot.yMax) * plot.innerHeight;
            return (
              <g key={tick}>
                <line x1={PADDING.left} x2={WIDTH - PADDING.right} y1={y} y2={y} stroke="var(--border)" strokeWidth={1} />
                <text x={PADDING.left - 8} y={y} textAnchor="end" dominantBaseline="middle" className="fill-muted-foreground text-[9px]">
                  {tick}
                </text>
              </g>
            );
          })}

          <line
            x1={PADDING.left}
            x2={WIDTH - PADDING.right}
            y1={plot.targetY}
            y2={plot.targetY}
            stroke="var(--rail)"
            strokeWidth={1}
            strokeDasharray="4 3"
          />
          <text x={WIDTH - PADDING.right} y={plot.targetY - 4} textAnchor="end" className="fill-muted-foreground text-[9px]">
            meta: {target}
          </text>

          <path d={plot.areaPath} fill="var(--chart-1)" opacity={0.1} stroke="none" />
          <path d={plot.linePath} fill="none" stroke="var(--chart-1)" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />

          {plot.points.length > 0 && (
            <circle
              cx={plot.points[plot.points.length - 1].x}
              cy={plot.points[plot.points.length - 1].y}
              r={5}
              fill="var(--chart-1)"
              stroke="var(--card)"
              strokeWidth={2}
            />
          )}

          {hovered && (
            <>
              <line x1={hovered.x} x2={hovered.x} y1={PADDING.top} y2={PADDING.top + plot.innerHeight} stroke="var(--rail)" strokeWidth={1} />
              <circle cx={hovered.x} cy={hovered.y} r={5} fill="var(--chart-1)" stroke="var(--card)" strokeWidth={2} />
            </>
          )}
        </svg>

        {hovered && (
          <div
            className="pointer-events-none absolute top-1 -translate-x-1/2 rounded-md border border-border bg-card px-2.5 py-1.5 text-xs shadow-sm"
            style={{ left: `${(hovered.x / WIDTH) * 100}%` }}
          >
            <p className="font-semibold tabular-nums">{hovered.snapshot.followers_count} seguidores</p>
            <p className="text-muted-foreground">{formatDateTime(hovered.snapshot.recorded_at)}</p>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() => setShowTable((v) => !v)}
        className="text-xs font-medium text-navy hover:underline"
      >
        {showTable ? "Ocultar tabla" : "Ver como tabla"}
      </button>

      {showTable && (
        <div className="overflow-x-auto rounded-md border border-border">
          <table className="w-full text-xs">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-2.5 py-1.5 text-left font-medium">Fecha</th>
                <th className="px-2.5 py-1.5 text-right font-medium">Seguidores</th>
                <th className="px-2.5 py-1.5 text-right font-medium">Siguiendo</th>
                <th className="px-2.5 py-1.5 text-right font-medium">Posts</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {[...snapshots].reverse().map((s) => (
                <tr key={s.id}>
                  <td className="px-2.5 py-1.5">{formatDateTime(s.recorded_at)}</td>
                  <td className="px-2.5 py-1.5 text-right tabular-nums">{s.followers_count}</td>
                  <td className="px-2.5 py-1.5 text-right tabular-nums">{s.following_count}</td>
                  <td className="px-2.5 py-1.5 text-right tabular-nums">{s.statuses_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
