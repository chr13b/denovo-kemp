/* Chart renderers: data -> SVG strings. No DOM needed, so it runs in node (static SVG files) and in the page.
 * Palette: validated with dataviz/scripts/validate_palette.js (3 slots, all-pairs, light + dark: PASS).
 * Aqua (Glu is orange, His-Asp is aqua) sits below 3:1 on the light surface -> relief rule: every mark is direct-labelled and a table view is provided.
 */
(function (root) {
  const BASES = {
    asp: { label: "Asp carboxylate base" },
    glu: { label: "Glu carboxylate base" },
    his: { label: "His–Asp dyad" },
    unk: { label: "Base not retrieved" },
  };
  const CSS = `
.viz{--surface:#fcfcfb;--t1:#0b0b0b;--t2:#52514e;--t3:#6f6e69;--grid:#ecebe7;--axis:#d3d2cd;
  --s-asp:#2a78d6;--s-glu:#eb6834;--s-his:#1baf7a;--s-unk:#9b9a95}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .viz{--surface:#1a1a19;--t1:#ffffff;--t2:#c3c2b7;--t3:#9a9990;--grid:#2c2c2a;--axis:#3e3e3b;
  --s-asp:#3987e5;--s-glu:#d95926;--s-his:#199e70;--s-unk:#7d7c77}}
:root[data-theme="dark"] .viz{--surface:#1a1a19;--t1:#ffffff;--t2:#c3c2b7;--t3:#9a9990;--grid:#2c2c2a;--axis:#3e3e3b;
  --s-asp:#3987e5;--s-glu:#d95926;--s-his:#199e70;--s-unk:#7d7c77}
.viz text{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.viz .bg{fill:var(--surface)} .viz .t1{fill:var(--t1)} .viz .t2{fill:var(--t2)} .viz .t3{fill:var(--t3)}
.viz .grid{stroke:var(--grid);stroke-width:1;fill:none} .viz .axis{stroke:var(--axis);stroke-width:1;fill:none}
.viz .hit{fill:transparent}
.viz .f-asp{fill:var(--s-asp)} .viz .f-glu{fill:var(--s-glu)} .viz .f-his{fill:var(--s-his)} .viz .f-unk{fill:var(--s-unk)}
.viz .k-asp{stroke:var(--s-asp)} .viz .k-glu{stroke:var(--s-glu)} .viz .k-his{stroke:var(--s-his)} .viz .k-unk{stroke:var(--s-unk)}
.viz .ring{stroke:var(--surface);stroke-width:2} .viz .hol{fill:var(--surface);stroke-width:2}
.viz .stem{stroke-width:2;stroke-linecap:round;opacity:.55}
.viz .ref{stroke:var(--axis);stroke-width:1;fill:none}
`;
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/\n/g, "&#10;");
  const fmt = (v) => (v >= 10 ? Math.round(v).toLocaleString("en-US") : String(Math.round(v * 10) / 10));
  const lg = Math.log10;
  const wrap = (W, H, title, body, label) =>
    `<svg xmlns="http://www.w3.org/2000/svg" class="viz" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="${esc(label)}"><style>${CSS}</style>` +
    `<rect class="bg" width="${W}" height="${H}"/>${body}</svg>`;
  const text = (x, y, s, cls = "t1", size = 12, extra = "") => `<text x="${x}" y="${y}" class="${cls}" font-size="${size}" ${extra}>${esc(s)}</text>`;
  const lines = (x, y, s, cls, size, lh) => String(s).split("  ").map((ln, i) => text(x, y + i * lh, ln, cls, size)).join("");
  const dot = (x, y, b, hollow, r = 5.5) => hollow ? `<circle cx="${x}" cy="${y}" r="${r}" class="hol k-${b}"/>` : `<circle cx="${x}" cy="${y}" r="${r}" class="f-${b} ring"/>`;
  const diamond = (x, y, b, hollow, r = 7) => `<polygon points="${x},${y - r} ${x + r},${y} ${x},${y + r} ${x - r},${y}" class="${hollow ? "hol k-" + b : "f-" + b + " ring"}"/>`;
  const square = (x, y, b, hollow, r = 5) => `<rect x="${x - r}" y="${y - r}" width="${2 * r}" height="${2 * r}" rx="1.5" class="${hollow ? "hol k-" + b : "f-" + b + " ring"}"/>`;
  const decades = (lo, hi) => { const a = []; for (let e = Math.ceil(lo); e <= hi; e++) a.push(e); return a; };
  const tick = (e) => (Math.pow(10, e)).toLocaleString("en-US");

  function legendBases(x, y, keys) {
    let s = "", cx = x;
    keys.forEach((k) => { s += `<circle cx="${cx}" cy="${y - 4}" r="5" class="f-${k}"/>` + text(cx + 10, y, BASES[k].label, "t2", 11.5); cx += 24 + BASES[k].label.length * 6.1; });
    return s;
  }

  /* ---------- A: design -> best variant dumbbell ---------- */
  function dumbbell(D) {
    const W = 900, L = 275, R = 775, rowH = 36, lmin = 0.6, lmax = 6.1;
    const X = (v) => L + ((lg(v) - lmin) / (lmax - lmin)) * (R - L);
    const groups = [["evo", "DIRECTED EVOLUTION (lab library screening)"], ["comp", "COMPUTATIONAL ONLY (no library screening)"]];
    let y = 122, body = "", rowsSvg = "", grid = "", n = 0;
    const layout = [];
    groups.forEach(([g, title]) => {
      layout.push({ header: title, y }); y += 26;
      D.rows.filter((r) => r.group === g).forEach((r) => { layout.push({ r, y: y + 12 }); y += rowH; });
      y += 10;
    });
    const H = y + 46;
    decades(lmin, lmax).forEach((e) => { grid += `<line class="grid" x1="${X(Math.pow(10, e))}" x2="${X(Math.pow(10, e))}" y1="102" y2="${H - 44}"/>` + text(X(Math.pow(10, e)), H - 26, tick(e), "t2", 11, 'text-anchor="middle"'); });
    body += text(14, 26, "From published design to best variant", "t1", 15, 'font-weight="600"');
    body += text(14, 45, "kcat/KM, M⁻¹ s⁻¹ (log scale). Colour = catalytic base. Values and sources: see the table view.", "t2", 12);
    body += legendBases(14, 68, ["asp", "glu", "his", "unk"]);
    let mk = 14; // marker key on its own row
    body += `<circle cx="${mk + 5}" cy="86" r="5" class="hol k-unk"/>` + text(mk + 16, 90, "design / start", "t2", 11.5);
    body += `<circle cx="${mk + 125}" cy="86" r="5.5" class="f-unk ring"/>` + text(mk + 137, 90, "best reported", "t2", 11.5);
    body += diamond(mk + 245, 86, "unk", true, 6) + text(mk + 257, 90, "derived or lower bound (≤ / ≥)", "t2", 11.5);
    body += grid;
    layout.forEach((it) => {
      if (it.header) { body += text(14, it.y + 4, it.header, "t2", 11, 'letter-spacing=".06em" font-weight="600"') + `<line class="grid" x1="14" x2="${W - 14}" y1="${it.y + 12}" y2="${it.y + 12}"/>`; return; }
      const r = it.r, cy = it.y;
      const hasS = r.start != null, hasE = r.end != null;
      const tip = `${r.name}\n${r.scaffold} · ${r.baseRes}\nstart: ${hasS ? (r.startKind === "derived" ? "≤" : "") + fmt(r.start) : "–"}  →  end: ${hasE ? (r.endKind === "derived" ? "≤" : r.endKind === "lower" ? "≥" : "") + fmt(r.end) : "–"}\n${r.src}${r.note ? "\n" + r.note : ""}`;
      body += `<g data-tip="${esc(tip)}">`;
      body += `<rect class="hit" x="0" y="${cy - 15}" width="${W}" height="${rowH}"/>`;
      body += text(14, cy - 1, r.name, "t1", 12.5, 'font-weight="600"') + text(14, cy + 13, `${r.scaffold} · ${r.baseRes}`, "t2", 11);
      if (hasS && hasE) body += `<line class="stem k-${r.base}" x1="${X(r.start)}" x2="${X(r.end)}" y1="${cy}" y2="${cy}"/>`;
      if (hasS) { body += r.startKind === "derived" ? diamond(X(r.start), cy, r.base, true, 6) : dot(X(r.start), cy, r.base, true, 5); body += text(X(r.start) - 10, cy + 4, (r.startKind === "derived" ? "≤" : "") + fmt(r.start), "t2", 11.5, 'text-anchor="end"'); }
      if (hasE) {
        body += (r.endKind === "derived" || r.endKind === "lower") ? diamond(X(r.end), cy, r.base, true, 6.5) : dot(X(r.end), cy, r.base, false, 5.5);
        body += text(X(r.end) + 11, cy + 4, (r.endKind === "derived" ? "≤" : r.endKind === "lower" ? "≥" : "") + fmt(r.end), "t1", 12, 'font-weight="600"');
      } else body += text(X(r.start) + 11, cy + 4, "no optimised variant in this set", "t3", 11);
      body += `</g>`;
    });
    body += text((L + R) / 2, H - 6, "kcat/KM (M⁻¹ s⁻¹)", "t2", 11.5, 'text-anchor="middle"');
    return wrap(W, H, "", body, "Dumbbell chart of kcat/KM from the original design to the best variant for each Kemp eliminase design, grouped by directed evolution versus computational-only optimisation");
  }

  /* ---------- B: catalytic constellation vs activity ---------- */
  function matrix(D) {
    const W = 1000, rowH = 50, top = 132;
    const cols = { name: 14, base: 142, pi: 290, polar: 482, side: 664, dot: 744 };
    const x0 = 744, x1 = 960, lmin = 0.6, lmax = 6.1;
    const X = (v) => x0 + ((lg(v) - lmin) / (lmax - lmin)) * (x1 - x0);
    const rows = D.matrix.slice().sort((a, b) => (b.best || 0) - (a.best || 0));
    const H = top + rows.length * rowH + 52;
    let body = text(14, 26, "Catalytic constellation vs best activity", "t1", 15, 'font-weight="600"');
    body += text(14, 45, "Rows sorted by best published kcat/KM. Tags: ·x observed in a ligand complex   ·d design papers (design numbering)   ·m modelled pose.", "t2", 12);
    body += legendBases(14, 68, ["asp", "glu", "his"]);
    const hy = top - 18;
    [["name", "Design"], ["base", "Base"], ["pi", "Aromatic π-contact"], ["polar", "Nitro / oxyanion H-bond"], ["side", "Base meets"]].forEach(([k, t]) => body += text(cols[k], hy, t, "t2", 11, 'font-weight="600"'));
    body += text(cols.dot, hy, "Best kcat/KM (M⁻¹ s⁻¹)", "t2", 11, 'font-weight="600"');
    body += `<line class="axis" x1="14" x2="${W - 14}" y1="${hy + 10}" y2="${hy + 10}"/>`;
    decades(lmin, lmax).forEach((e) => { const x = X(Math.pow(10, e)); body += `<line class="grid" x1="${x}" x2="${x}" y1="${hy + 10}" y2="${top + rows.length * rowH}"/>` + text(x, top + rows.length * rowH + 16, e >= 3 ? (e === 3 ? "1k" : e === 4 ? "10k" : e === 5 ? "100k" : "1M") : tick(e), "t2", 11, 'text-anchor="middle"'); });
    rows.forEach((r, i) => {
      const y = top + i * rowH, cy = y + 16;
      const tip = `${r.name} (${r.sub})\nbase: ${r.baseTxt.replace(/  /g, " ")}\nπ: ${r.pi.replace(/  /g, " ")}\npolar: ${r.polar}\nbase contacts: ${r.side}\nbest: ${r.best ? fmt(r.best) : "no kinetics found"} – ${r.bestNote}`;
      body += `<g data-tip="${esc(tip)}"><rect class="hit" x="0" y="${y - 4}" width="${W}" height="${rowH}"/>`;
      body += `<line class="grid" x1="14" x2="${W - 14}" y1="${y + rowH - 6}" y2="${y + rowH - 6}"/>`;
      body += text(cols.name, cy, r.name, "t1", 12.5, 'font-weight="600"') + text(cols.name, cy + 14, r.sub, "t2", 11);
      body += `<circle cx="${cols.base + 5}" cy="${cy - 4}" r="5" class="f-${r.base}"/>` + lines(cols.base + 16, cy, r.baseTxt, "t1", 11.5, 14);
      body += lines(cols.pi, cy, r.pi, /^(none|not)/.test(r.pi) ? "t3" : "t1", 11.5, 14);
      body += lines(cols.polar, cy, r.polar, /^(none|not)/.test(r.polar) ? "t3" : "t1", 11.5, 14);
      body += text(cols.side, cy, r.side, /^(n\/d|no )/.test(r.side) ? "t3" : "t1", 11.5);
      if (r.best) {
        body += `<line class="stem k-${r.base}" x1="${x0}" x2="${X(r.best)}" y1="${cy - 4}" y2="${cy - 4}"/>` + dot(X(r.best), cy - 4, r.base, r.name === "1A53-2", 5.5);
        body += text(X(r.best) + 10, cy, fmt(r.best), "t1", 12, 'font-weight="600"');
      } else body += text(x0, cy, "no kinetics found", "t3", 11.5);
      body += `</g>`;
    });
    body += text(14, H - 8, "KE59 side is n/d: the 5,7-dichloro and benzotriazole ligands are symmetric up to numbering. KempTIM best value is from a related variant; Des27.7 + one extra residue is >10⁵.", "t3", 11);
    return wrap(W, H, "", body, "Table-chart comparing catalytic base, aromatic contact and hydrogen-bond donors of each Kemp eliminase design against its best published catalytic efficiency");
  }

  /* ---------- C: start vs best scatter ---------- */
  const SC_LAB = { // id: [dx, dy, anchor, short label]
    KE07: [12, 4, "start", "KE07"], KE70: [-12, 4, "end", "KE70"], KE59: [12, 4, "start", "KE59"], HG3: [-12, 4, "end", "HG3 → HG3.17"],
    HGE: [12, 4, "start", "HG3 ensemble"], KEE: [-12, 4, "end", "KE70 ensemble"], D27: [12, 4, "start", "Des27 → Des27.7"],
    D61: [12, 4, "start", "Des61"], TIME: [-4, -14, "start", "KempTIM ensemble"] };
  function scatter(D) {
    const W = 900, H = 620, ml = 84, mr = 40, mt = 108, mb = 66;
    const xmin = 1, xmax = 5, ymin = 2, ymax = 6;
    const X = (v) => ml + ((lg(v) - xmin) / (xmax - xmin)) * (W - ml - mr), Y = (v) => H - mb - ((lg(v) - ymin) / (ymax - ymin)) * (H - mt - mb);
    let body = text(14, 26, "Starting activity vs best activity", "t1", 15, 'font-weight="600"');
    body += text(14, 45, "kcat/KM, M⁻¹ s⁻¹ (log–log). Points above the diagonal gained activity; fold-gain guides at ×100 and ×1,000.", "t2", 12);
    body += legendBases(14, 68, ["asp", "glu", "his", "unk"]);
    decades(xmin, xmax).forEach((e) => { const x = X(Math.pow(10, e)); body += `<line class="grid" x1="${x}" x2="${x}" y1="${mt}" y2="${H - mb}"/>` + text(x, H - mb + 18, tick(e), "t2", 11, 'text-anchor="middle"'); });
    decades(ymin, ymax).forEach((e) => { const y = Y(Math.pow(10, e)); body += `<line class="grid" x1="${ml}" x2="${W - mr}" y1="${y}" y2="${y}"/>` + text(ml - 8, y + 4, tick(e), "t2", 11, 'text-anchor="end"'); });
    body += `<rect x="${ml}" y="${mt}" width="${W - ml - mr}" height="${H - mt - mb}" class="axis"/>`;
    const guide = (k, label) => { // y = k*x clipped to the plot
      const xa = Math.max(Math.pow(10, xmin), Math.pow(10, ymin) / k), xb = Math.min(Math.pow(10, xmax), Math.pow(10, ymax) / k);
      body += `<line class="ref" x1="${X(xa)}" y1="${Y(k * xa)}" x2="${X(xb)}" y2="${Y(k * xb)}"/>` + text(X(xb) - 6, Y(k * xb) + (k === 1 ? -6 : 14), label, "t3", 11, 'text-anchor="end"');
    };
    guide(1, "no gain"); guide(100, "×100"); guide(1000, "×1,000");
    body += text((ml + W - mr) / 2, H - 14, "Original design kcat/KM", "t2", 12, 'text-anchor="middle"');
    body += text(18, (mt + H - mb) / 2, "Best kcat/KM", "t2", 12, `text-anchor="middle" transform="rotate(-90 18 ${(mt + H - mb) / 2})"`);
    D.rows.filter((r) => r.start != null && r.end != null && r.endKind !== "lower").forEach((r) => {
      const x = X(r.start), y = Y(r.end), hollow = r.endKind === "derived" || r.startKind === "derived";
      const shape = r.group === "evo" ? dot(x, y, r.base, hollow, 6) : diamond(x, y, r.base, hollow, 8);
      const tip = `${r.name}\n${r.scaffold} · ${r.baseRes}\n${r.group === "evo" ? "directed evolution" : "computational only"}\n${(r.startKind === "derived" ? "≤" : "") + fmt(r.start)} → ${(r.endKind === "derived" ? "≤" : "") + fmt(r.end)}  (×${fmt(r.end / r.start)})\n${r.src}`;
      const lab = SC_LAB[r.id] || [12, 4, "start", r.name];
      body += `<g data-tip="${esc(tip)}"><circle class="hit" cx="${x}" cy="${y}" r="14"/>${shape}</g>`;
      body += text(x + lab[0], y + lab[1], lab[3], "t1", 11.5, `text-anchor="${lab[2]}"`);
    });
    body += dot(14 + 5, 86, "unk", false, 5.5) + text(14 + 16, 90, "directed evolution", "t2", 11.5);
    body += diamond(14 + 150, 86, "unk", false, 7) + text(14 + 164, 90, "computational only", "t2", 11.5);
    body += dot(14 + 290, 86, "unk", true, 5.5) + text(14 + 302, 90, "hollow = derived value", "t2", 11.5);
    return wrap(W, H, "", body, "Log-log scatter of each design's original kcat/KM against its best published kcat/KM, coloured by catalytic base, with shapes for evolution versus computational-only optimisation");
  }

  /* ---------- D: crystal geometry vs activity ---------- */
  const GEO = {
    "7K4Q_A": { g: "HG3", b: "asp" }, "5RGA_A": { g: "HG3", b: "asp" }, "3NYD_A": { g: "HG-2", b: "asp" },
    "7K4Z_A": { g: "HG3.17", b: "asp" }, "5RGE_A": { g: "HG3.17", b: "asp" }, "3NZ1_A": { g: "1A53-2", b: "glu", sq: true },
    "3UZ5_A": { g: "KE59 R13", b: "glu" }, "3UZJ_A": { g: "KE59 R13", b: "glu" },
    "Des27.7_sub": { g: "Des27.7", b: "asp", hol: true }, "Des27_sub": { g: "Des27", b: "asp", hol: true },
  };
  const GLAB = { // [panel][group] -> [dx, dy, anchor, optional text]; null = no label
    0: { "HG3": [-10, 18, "end"], "HG-2": [-4, -12, "end"], "HG3.17": [-10, -10, "end"], "1A53-2": [-10, 18, "end"], "KE59 R13": [10, -10, "start"], "Des27.7": [10, 4, "start"], "Des27": [10, 4, "start"] },
    1: { "HG3": [0, -14, "middle", "HG3 / HG-2"], "HG-2": null, "HG3.17": [-12, 4, "end"], "1A53-2": [-12, 4, "end"], "KE59 R13": [-4, -14, "start"], "Des27.7": [12, 4, "start"], "Des27": [12, 4, "start"] },
  };
  function geometry(D) {
    const W = 920, H = 580, mt = 124, mb = 70, ml = 78;
    const pw = 340, gap = 66;
    const ymin = 1, ymax = 6;
    const Y = (v) => H - mb - ((lg(v) - ymin) / (ymax - ymin)) * (H - mt - mb);
    const panels = [
      { x0: ml, lo: 2.0, hi: 3.0, key: "base_dist", title: "Base to the TSA ring N", unit: "Å", ticks: [2.0, 2.25, 2.5, 2.75, 3.0] },
      { x0: ml + pw + gap, lo: 3.4, hi: 6.6, key: "pi_dist", title: "Nearest aromatic ring to the TSA benzo ring", unit: "Å", ticks: [3.5, 4.5, 5.5, 6.5] },
    ];
    let body = text(14, 26, "Crystal geometry vs activity", "t1", 15, 'font-weight="600"');
    body += text(14, 45, "Each point is one structure with a published kcat/KM for that variant. Hollow = modelled substrate pose, square = base meets N1 not N3.", "t2", 12);
    body += legendBases(14, 68, ["asp", "glu"]);
    body += dot(19, 86, "unk", true, 5.5) + text(30, 90, "modelled substrate pose (not a crystal)", "t2", 11.5);
    body += square(300, 86, "unk", false, 5) + text(312, 90, "base meets N1, not N3", "t2", 11.5);
    panels.forEach((p, pi) => {
      const X = (v) => p.x0 + ((v - p.lo) / (p.hi - p.lo)) * pw;
      body += text(p.x0, mt - 14, p.title, "t1", 12.5, 'font-weight="600"');
      decades(ymin, ymax).forEach((e) => { const y = Y(Math.pow(10, e)); body += `<line class="grid" x1="${p.x0}" x2="${p.x0 + pw}" y1="${y}" y2="${y}"/>` + (pi === 0 ? text(p.x0 - 8, y + 4, tick(e), "t2", 11, 'text-anchor="end"') : ""); });
      p.ticks.forEach((t) => body += `<line class="grid" x1="${X(t)}" x2="${X(t)}" y1="${mt}" y2="${H - mb}"/>` + text(X(t), H - mb + 18, String(t), "t2", 11, 'text-anchor="middle"'));
      body += `<rect x="${p.x0}" y="${mt}" width="${pw}" height="${H - mb - mt}" class="axis"/>` + text(p.x0 + pw / 2, H - mb + 40, `distance (${p.unit})`, "t2", 11.5, 'text-anchor="middle"');
      const done = {};
      D.geometry.forEach((g) => {
        const m = GEO[g.structure]; if (!m) return;
        const x = X(g[p.key]), y = Y(g.kcat_KM);
        const shape = m.sq ? square(x, y, m.b, m.hol, 5.5) : dot(x, y, m.b, m.hol, 5.5);
        const tip = `${g.structure} · ${g.variant}\nkcat/KM ${fmt(g.kcat_KM)} (${g.source})${g.caveat ? "\n" + g.caveat : ""}\nbase: ${g.base_res} → ${g.base_contacts}, ${g.base_dist} Å\naromatic: ${g.pi_res}, ${g.pi_dist} Å, ring tilt ${g.pi_angle}°`;
        body += `<g data-tip="${esc(tip)}"><circle class="hit" cx="${x}" cy="${y}" r="13"/>${shape}</g>`;
        if (!done[m.g]) { done[m.g] = 1; const l = GLAB[pi][m.g]; if (l !== null) { const L = l || [10, 4, "start"]; body += text(x + L[0], y + L[1], L[3] || m.g, "t1", 11.5, `text-anchor="${L[2]}"`); } }
      });
    });
    body += text(18, (mt + H - mb) / 2, "kcat/KM of that variant (M⁻¹ s⁻¹, log)", "t2", 12, `text-anchor="middle" transform="rotate(-90 18 ${(mt + H - mb) / 2})"`);
    body += text(14, H - 8, "HG3.17 = 230,000 comes from a web summary of Blomberg 2013, not read in the paper text. KE59 uses 5-nitrobenzisoxazole; HG3 and HG3.17 conditions differ.", "t3", 11);
    return wrap(W, H, "", body, "Two-panel scatter of catalytic-base distance and aromatic-ring distance in crystal structures against each variant's kcat/KM");
  }

  const api = { CSS, BASES, dumbbell, matrix, scatter, geometry, esc, fmt };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.KempCharts = api;
})(typeof window !== "undefined" ? window : globalThis);
