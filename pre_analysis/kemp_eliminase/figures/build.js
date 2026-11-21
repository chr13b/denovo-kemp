// node figures/build.js  -> figures/svg/*.svg and figures/kemp_design_vs_activity.html
const fs = require("fs"), path = require("path");
const C = require("./charts.js");
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "data", "data.json"), "utf8"));

const charts = { "1_design_to_best": C.dumbbell(D), "2_constellation_vs_activity": C.matrix(D), "3_start_vs_best": C.scatter(D), "4_geometry_vs_activity": C.geometry(D) };
fs.mkdirSync(path.join(__dirname, "svg"), { recursive: true });
for (const [k, v] of Object.entries(charts)) fs.writeFileSync(path.join(__dirname, "svg", k + ".svg"), v);

const { esc, fmt } = C;
const table = (head, rows) => `<div class="tw"><table><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
const kind = { design: "", best: "", derived: "≤ ", lower: "≥ ", none: "" };
const tA = table(["Design", "Group", "Scaffold · base", "Original design", "Best", "Source", "Note"], D.rows.map((r) => [r.name, r.group === "evo" ? "directed evolution" : "computational only", `${r.scaffold} · ${r.baseRes}`,
  r.start == null ? "–" : (r.startKind === "derived" ? "≤ " : "") + fmt(r.start), r.end == null ? "–" : kind[r.endKind] + fmt(r.end), r.src, r.note]));
const tB = table(["Design", "Base", "Aromatic π-contact", "Nitro / oxyanion H-bond", "Base meets", "Best kcat/KM", "Note"], D.matrix.map((m) => [`${m.name} (${m.sub})`, m.baseTxt.replace(/  /g, " "), m.pi.replace(/  /g, " "), m.polar, m.side, m.best ? fmt(m.best) : "no kinetics found", m.bestNote]));
const tD = table(["Structure", "Variant", "kcat/KM", "Base · contact · distance (Å)", "Nearest aromatic · distance (Å) · tilt", "Source", "Caveat"], D.geometry.map((g) => [g.structure, g.variant, fmt(g.kcat_KM), `${g.base_res} · ${g.base_contacts} · ${g.base_dist}`, `${g.pi_res} · ${g.pi_dist} · ${g.pi_angle}°`, g.source, g.caveat]));

const page = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kemp eliminase design vs activity</title>
<style>
:root{color-scheme:light;--bg:#f7f6f3;--card:#fcfcfb;--t1:#0b0b0b;--t2:#52514e;--t3:#6f6e69;--line:#e6e5e1;--accent:#2a78d6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#121211;--card:#1a1a19;--t1:#fff;--t2:#c3c2b7;--t3:#9a9990;--line:#2c2c2a;--accent:#3987e5}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#121211;--card:#1a1a19;--t1:#fff;--t2:#c3c2b7;--t3:#9a9990;--line:#2c2c2a;--accent:#3987e5}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--t1);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:28px 16px 64px}
header{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
h1{font-size:24px;margin:0 0 6px;font-weight:650;letter-spacing:-.01em} .lede{color:var(--t2);margin:0 0 22px;max-width:70ch}
button.theme{background:var(--card);color:var(--t2);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font:inherit;font-size:13px;cursor:pointer}
.finds{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin:0 0 26px}
.find{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px} .find b{display:block;font-size:13px;color:var(--t2);font-weight:600;margin-bottom:4px}
.find p{margin:0;font-size:14px}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:0 0 20px;padding:14px 12px 12px}
section h2{font-size:15px;margin:2px 4px 4px;font-weight:650} section p.cap{margin:0 4px 8px;color:var(--t2);font-size:13.5px}
.fig{overflow-x:auto} .fig svg{display:block;width:100%;min-width:640px;height:auto}
details{margin:8px 4px 0} summary{cursor:pointer;color:var(--accent);font-size:13px}
.tw{overflow-x:auto;margin-top:8px} table{border-collapse:collapse;font-size:12.5px;min-width:720px} th,td{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top} th{color:var(--t2);font-weight:600}
.notes{color:var(--t2);font-size:13px} .notes li{margin:4px 0}
#tip{position:fixed;z-index:10;pointer-events:none;background:var(--card);color:var(--t1);border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:12.5px;line-height:1.45;max-width:340px;white-space:pre-line;box-shadow:0 6px 24px rgba(0,0,0,.18);display:none}
</style></head><body><main>
<header><div><h1>Kemp eliminase designs vs catalytic activity</h1>
<p class="lede">Published kcat/KM for each design family set against its catalytic residues and the geometry seen in crystal structures. Hover any mark for the value, source and caveats; every chart has a table view.</p></div>
<button class="theme" id="theme" aria-label="Toggle light and dark theme">Theme</button></header>

<div class="finds">
<div class="find"><b>Where designs start</b><p>Every design began at 12–210 M⁻¹s⁻¹ (1A53-2: 64), whatever its base. Optimised variants then span 2,600 to 230,000.</p></div>
<div class="find"><b>Computational only is close</b><p>With no library screening, Des27.7 (12,700), KempTIM after ensemble redesign (32,000) and Des27.7 plus one engineered residue (>100,000) are within roughly 2–18× of HG3.17 (230,000).</p></div>
<div class="find"><b>Static geometry does not separate them</b><p>Base to ring N is 2.25–2.72 Å from 125 to 230,000 M⁻¹s⁻¹. Des27 and Des27.7 differ by about 100× in activity yet match to 0.01 Å (2.72 vs 2.71 Å) and 0.04 Å (3.96 vs 3.92 Å).</p></div>
<div class="find"><b>Tight stacking is not required</b><p>IGPS designs sit 3.6–4.0 Å from an aromatic ring; HG3 is 5.1 Å and HG3.17 6.3 Å, the most active enzyme here. (HG3.17 value unverified in the paper text.)</p></div>
</div>

<section><h2>1 · From original design to best variant</h2><p class="cap">Dumbbells show each lineage's start and end on one log axis, split by how the gain was obtained.</p>
<div class="fig">${charts["1_design_to_best"]}</div><details><summary>Table view</summary>${tA}</details></section>

<section><h2>2 · Catalytic residues against best activity</h2><p class="cap">The theozyme components (base, aromatic contact, nitro-side hydrogen bond) for each design, ordered by activity.</p>
<div class="fig">${charts["2_constellation_vs_activity"]}</div><details><summary>Table view</summary>${tB}</details></section>

<section><h2>3 · Does the starting activity predict the end point?</h2><p class="cap">Original design kcat/KM against best kcat/KM. Diamonds are computational-only optimisation, circles directed evolution.</p>
<div class="fig">${charts["3_start_vs_best"]}</div><details><summary>Table view (same data as chart 1)</summary>${tA}</details></section>

<section><h2>4 · Crystal geometry against activity</h2><p class="cap">Catalytic-contact distances measured in the substrate-aligned structures, plotted against the kcat/KM of the exact variant.</p>
<div class="fig">${charts["4_geometry_vs_activity"]}</div><details><summary>Table view</summary>${tD}</details></section>

<section><h2>Read with care</h2><ul class="notes">
<li>Conditions (pH, temperature, substrate, buffer) differ between papers; compare orders of magnitude, not small differences.</li>
<li>HG3.17 = 230,000 is from a web summary of Blomberg 2013, not the paper text. "≤" values are my calculation from a stated fold-change (125 × 250, 57 × 250, 32,000 ÷ 1,600), not reported numbers.</li>
<li>KE59 uses 5-nitrobenzisoxazole (60,430); with 5,7-dichlorobenzisoxazole the same variant reaches 573,090 and is not comparable.</li>
<li>Geometry is from TS-analog complexes (6NT, 3NY, 0CU, 0CT) or modelled substrate poses, not the true transition state. About ten structures with a matching kinetic value: this shows a lack of correlation, not proof of its absence.</li>
<li>Source files: <code>figures/data/data.json</code>, <code>designs.csv</code>, <code>geometry.csv</code>; standalone charts in <code>figures/svg/</code>.</li></ul></section>
</main><div id="tip" role="tooltip"></div>
<script>
(function(){
  var tip=document.getElementById('tip');
  function show(e){var t=e.target.closest('[data-tip]'); if(!t){tip.style.display='none';return}
    tip.textContent=t.getAttribute('data-tip'); tip.style.display='block';
    var x=e.clientX+14,y=e.clientY+14,r=tip.getBoundingClientRect();
    if(x+r.width>innerWidth-8)x=e.clientX-r.width-14; if(y+r.height>innerHeight-8)y=e.clientY-r.height-14; tip.style.left=x+'px';tip.style.top=y+'px';}
  document.addEventListener('mousemove',show); document.addEventListener('mouseleave',function(){tip.style.display='none'});
  var b=document.getElementById('theme'),root=document.documentElement;
  try{var s=localStorage.getItem('kemp-theme'); if(s)root.setAttribute('data-theme',s)}catch(e){}
  b.addEventListener('click',function(){var cur=root.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');
    var nx=cur==='dark'?'light':'dark'; root.setAttribute('data-theme',nx); try{localStorage.setItem('kemp-theme',nx)}catch(e){}});
})();
</script></body></html>`;
fs.writeFileSync(path.join(__dirname, "kemp_design_vs_activity.html"), page);
console.log("wrote", Object.keys(charts).length, "svgs + html");
