import { useMemo, useState } from "react";
import { VARIANTS } from "../data/variants.js";

/* ---- helpers ---- */
function fam(sig) {
  const s = (sig || "").toLowerCase();
  if (s.includes("conflict")) return "Conflicting";
  if (s.includes("pathogenic")) return "Pathogenic";
  if (s.includes("benign")) return "Benign";
  if (s.includes("uncertain")) return "VUS";
  return "Other";
}
function badgeClass(f) {
  return f === "Pathogenic" ? "b-path" : f === "Benign" ? "b-benign" : f === "VUS" ? "b-vus" : f === "Conflicting" ? "b-conf" : "b-other";
}
function leanClass(L) {
  return L === "Lean pathogenic" ? "lp" : L === "Lean benign" ? "lb" : L === "Conflicting signals" ? "lc" : L.indexOf("Insufficient") === 0 ? "lw" : "lz";
}
function leanShort(L) {
  return L === "Insufficient (rarity only)" ? "Rarity only" : L === "Insufficient (frequency unreliable here)" ? "Freq unreliable" : L;
}

/* stable default order: bring representative alleles to the top */
const SORTED = (() => {
  const picks = ["c.1096G>A", "c.863A>T", "c.514G>T", "c.1200A>C", "c.187C>T", "c.1130"];
  return [...VARIANTS].sort((a, b) => {
    const ai = picks.findIndex((p) => a.c.startsWith(p));
    const bi = picks.findIndex((p) => b.c.startsWith(p));
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });
})();

function AfCell({ v }) {
  if (v.fs === "found") return <span className="af-num">{v.af}</span>;
  if (v.fs === "absent") return <span className="af-num af-absent">absent</span>;
  return <span className="af-unmapped">unmapped</span>;
}
function AmCell({ v }) {
  if (!v.am) return <span className="am-cell am-na">n/a</span>;
  const cls = v.amc === "likely_pathogenic" ? "am-p" : v.amc === "likely_benign" ? "am-b" : "am-x";
  const lab = v.amc === "likely_pathogenic" ? "likely path" : v.amc === "likely_benign" ? "likely benign" : "ambiguous";
  return <span className={"am-cell " + cls}>{v.am} <span className="lab">{lab}</span></span>;
}

/* frequency-vs-pathogenicity dot strip, built as an SVG string */
function buildChart() {
  const found = VARIANTS.filter((v) => v.fs === "found").map((v) => ({ af: parseFloat(v.af), f: fam(v.sig) })).filter((d) => d.af > 0);
  const lanes = ["Benign", "VUS", "Pathogenic"];
  const laneColor = { Benign: "#3f9d57", VUS: "#c79138", Pathogenic: "#d1554a" };
  const W = 920, H = 300, mL = 96, mR = 24, mT = 20, mB = 42, x0 = mL, x1 = W - mR, lo = -6, hi = 0;
  const X = (v) => x0 + (Math.log10(v) - lo) / (hi - lo) * (x1 - x0);
  const laneY = (i) => mT + (i + 0.5) * ((H - mT - mB) / lanes.length);
  let svg = '<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="Allele frequency by classification, logarithmic axis" style="max-width:100%;height:auto;font-family:Inter,sans-serif;">';
  for (let e = lo; e <= hi; e++) {
    const x = X(Math.pow(10, e));
    svg += '<line class="grid-line" x1="' + x + '" y1="' + mT + '" x2="' + x + '" y2="' + (H - mB) + '"/>';
    svg += '<text class="axis-label" x="' + x + '" y="' + (H - mB + 16) + '" text-anchor="middle">1e' + e + "</text>";
  }
  svg += '<text class="axis-label" x="' + ((x0 + x1) / 2) + '" y="' + (H - 6) + '" text-anchor="middle">gnomAD allele frequency (log scale)</text>';
  [[0.0001, "PM2"], [0.01, "BS1"], [0.05, "BA1"]].forEach((p) => {
    const x = X(p[0]);
    svg += '<line class="thr-line" x1="' + x + '" y1="' + (mT - 4) + '" x2="' + x + '" y2="' + (H - mB) + '"/>';
    svg += '<text class="thr-label" x="' + x + '" y="' + (mT - 8) + '" text-anchor="middle">' + p[1] + "</text>";
  });
  lanes.forEach((ln, i) => {
    const y = laneY(i);
    svg += '<text class="lane-label" x="' + (mL - 14) + '" y="' + (y + 4) + '" text-anchor="end">' + ln + "</text>";
    const pts = found.filter((d) => d.f === ln);
    pts.forEach((d) => {
      const jy = y + (Math.random() - 0.5) * 26;
      svg += '<circle cx="' + X(d.af).toFixed(1) + '" cy="' + jy.toFixed(1) + '" r="3" fill="' + laneColor[ln] + '" fill-opacity="0.68"/>';
    });
    svg += '<text class="axis-label" x="' + x1 + '" y="' + (y - 14) + '" text-anchor="end">' + pts.length + " variants</text>";
  });
  svg += "</svg>";
  return svg;
}

export default function Data() {
  const [query, setQuery] = useState("");
  const [classFilter, setClassFilter] = useState("all");
  const [leanFilter, setLeanFilter] = useState("");

  const chartSvg = useMemo(buildChart, []);

  const stats = useMemo(() => {
    let found = 0, absent = 0, unmapped = 0, insuf = 0, vlp = 0;
    const lc = {};
    VARIANTS.forEach((v) => {
      if (v.fs === "found") found++; else if (v.fs === "absent") absent++; else unmapped++;
      lc[v.lean] = (lc[v.lean] || 0) + 1;
      if (v.lean.indexOf("Insufficient") === 0) insuf++;
      if (v.lean === "Lean pathogenic" && fam(v.sig) === "VUS") vlp++;
    });
    return {
      found, absent, unmapped, vlp,
      lp: lc["Lean pathogenic"] || 0,
      lb: lc["Lean benign"] || 0,
      lc: lc["Conflicting signals"] || 0,
      insuf,
      none: lc["No information"] || 0,
    };
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return SORTED.filter((v) => {
      const f = fam(v.sig);
      if (classFilter !== "all" && f !== classFilter) return false;
      if (leanFilter) {
        if (leanFilter === "Insufficient") { if (v.lean.indexOf("Insufficient") !== 0) return false; }
        else if (v.lean !== leanFilter) return false;
      }
      if (!q) return true;
      return (v.c + " " + v.p + " " + v.sig + " " + v.lean).toLowerCase().includes(q);
    });
  }, [query, classFilter, leanFilter]);

  const shown = filtered.slice(0, 120);
  const classChips = ["all", "Pathogenic", "VUS", "Benign", "Conflicting"];
  const leanStats = [
    { key: "Lean pathogenic", cls: "p", n: stats.lp, label: "Lean pathogenic" },
    { key: "Lean benign", cls: "b", n: stats.lb, label: "Lean benign" },
    { key: "Conflicting signals", cls: "c", n: stats.lc, label: "Conflicting signals" },
    { key: "Insufficient", cls: "w", n: stats.insuf, label: "Insufficient evidence" },
    { key: "No information", cls: "z", n: stats.none, label: "No information" },
  ];
  const toggleLean = (k) => setLeanFilter((cur) => (cur === k ? "" : k));

  return (
    <>
      <header className="page-header wrap">
        <p className="eyebrow">A look at the data</p>
        <h1>Data</h1>
        <p className="lede">The 566-variant SERPINA1 dataset, its gnomAD frequency signal, AlphaMissense predictions, and the two-axis provisional lean the engine derives.</p>
      </header>

      <section className="reveal">
        <div className="wrap">
          <h2>Rarity tracks with pathogenicity</h2>
          <p className="lede narrow" style={{ marginBottom: "36px" }}>Each dot is one variant with a gnomAD allele frequency, placed on a shared logarithmic axis. The dashed lines are the ACMG frequency thresholds the estimator applies.</p>
          <div className="chart-shell glass">
            <div dangerouslySetInnerHTML={{ __html: chartSvg }} />
            <div className="chart-legend">
              <span><b>BA1</b> stand-alone benign, AF &gt; 0.05</span>
              <span><b>BS1</b> strong benign, AF &gt; 0.01</span>
              <span><b>PM2</b> supporting, AF &lt; 0.0001</span>
            </div>
          </div>
          <p className="finding"><b>{stats.found}</b> variants carry a real gnomAD frequency. Benign calls gather at the common end, pathogenic calls at the rare end. The relationship is a property of the joined data, not an assumption fed into it.</p>
        </div>
      </section>

      <section className="reveal">
        <div className="wrap">
          <h2>The provisional lean engine</h2>
          <p className="lede narrow" style={{ marginBottom: "22px" }}>Two mechanical axes, combined per variant: population rarity from gnomAD, and the AlphaMissense in-silico prediction. Rarity on its own is supporting only, since almost every variant in this gene is rare. And because the Z and S alleles are common yet pathogenic founder variants, population frequency is never allowed to call benign on its own here. A lean appears only when the two axes genuinely agree or conflict.</p>

          <div className="lean-summary">
            {leanStats.map((s) => (
              <button
                key={s.key}
                className={"lean-stat " + s.cls}
                aria-pressed={leanFilter === s.key}
                onClick={() => toggleLean(s.key)}
              >
                <span className="n">{s.n}</span>
                <span className="l">{s.label}</span>
              </button>
            ))}
          </div>

          <p className="lean-highlight"><b>{stats.vlp}</b> variants that ClinVar still calls uncertain lean pathogenic here on both axes at once. Those are the clearest triage candidates. Tellingly, the Z allele itself lands in <b>insufficient</b>: common enough to fool a frequency filter and ambiguous to AlphaMissense, so the engine refuses to guess. It surfaces its disagreements with ClinVar rather than hiding them.</p>

          <div className="tool glass">
            <div className="tool-head">
              <div className="search-row">
                <div>
                  <label className="sr" htmlFor="q">Search variant</label>
                  <input id="q" type="search" placeholder="e.g. Glu366 or c.1096 or 172" autoComplete="off" value={query} onChange={(e) => setQuery(e.target.value)} />
                </div>
                <div>
                  <label className="sr">Filter by ClinVar class</label>
                  <div className="chips">
                    {classChips.map((c) => (
                      <button key={c} className="chip" aria-pressed={classFilter === c} onClick={() => setClassFilter(c)}>
                        {c === "all" ? "All" : c}
                      </button>
                    ))}
                  </div>
                </div>
                <span className="count">{filtered.length} of {VARIANTS.length}</span>
              </div>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr><th>Variant (cDNA)</th><th>Protein</th><th>ClinVar call</th><th>gnomAD AF</th><th>AlphaMissense</th><th>Provisional lean</th></tr>
                </thead>
                <tbody>
                  {shown.map((v, i) => {
                    const f = fam(v.sig);
                    return (
                      <tr key={v.c + "|" + i}>
                        <td className="mono">{v.c}</td>
                        <td className="mono" style={{ color: "var(--muted)" }}>{v.p || "-"}</td>
                        <td><span className={"badge " + badgeClass(f)}>{v.sig}</span></td>
                        <td><AfCell v={v} /></td>
                        <td><AmCell v={v} /></td>
                        <td><span className={"lean-badge " + leanClass(v.lean)}>{leanShort(v.lean)}</span></td>
                      </tr>
                    );
                  })}
                  {shown.length === 0 && (
                    <tr><td colSpan={6} style={{ color: "var(--muted)", textAlign: "center", padding: "28px" }}>No variant matches that search.</td></tr>
                  )}
                  {filtered.length > 120 && (
                    <tr><td colSpan={6} style={{ color: "var(--muted)", fontSize: "0.82rem", textAlign: "center", padding: "16px" }}>Showing first 120. Refine the search to see more.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="tool-note">Every lean is <strong>provisional</strong>. It combines the frequency code (<code>BA1 / BS1 / PM2_Supporting</code>) with the AlphaMissense code (<code>PP3 / BP4</code>) only. The judgment codes that actually resolve a variant (PS3, PP1, PM3, BS4, PS4, functional and segregation evidence) need a human and are never assessed. {stats.found} found, {stats.absent} confirmed absent, {stats.unmapped} unmapped by frequency.</div>
          </div>
        </div>
      </section>
    </>
  );
}
