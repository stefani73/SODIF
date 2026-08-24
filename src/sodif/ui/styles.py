"""SODIF visual system kept local and dependency-free."""

PRODUCT_STYLES = """
<style>
:root {
    --ink: #10233f;
    --muted: #607086;
    --line: #dce4ec;
    --surface: #ffffff;
    --canvas: #f4f7fa;
    --teal: #087f8c;
    --teal-dark: #05606b;
    --navy: #0b1d35;
    --success: #087a64;
    --warning: #a8660c;
    --danger: #b33b47;
}
html, body, [class*="css"] { font-family: Inter, "Segoe UI", Arial, sans-serif; }
.stApp {
    color: var(--ink);
    background:
        radial-gradient(circle at 95% 0%, rgba(8,127,140,.09), transparent 28rem),
        var(--canvas);
}
header[data-testid="stHeader"], #MainMenu, footer { display: none; }
.block-container { max-width: 1220px; padding: 1.8rem 2.5rem 5rem; }
.sodif-header {
    display:flex; align-items:center; justify-content:space-between; margin-bottom:.75rem;
}
.sodif-brand { display:flex; align-items:center; gap:.72rem; }
.sodif-mark {
    width:34px; height:34px; display:grid; place-items:center; transform:rotate(45deg);
    border:1px solid rgba(8,127,140,.35); border-radius:10px; background:#fff;
    box-shadow:0 7px 20px rgba(16,35,63,.08);
}
.sodif-mark i {
    width:12px; height:12px; background:var(--teal); border-radius:3px; display:block;
}
.sodif-wordmark {
    font-size:1.08rem; font-weight:800; letter-spacing:.14em; color:var(--navy);
}
.sodif-trust-chip {
    display:flex; align-items:center; gap:.5rem; color:#4d6076; background:rgba(255,255,255,.75);
    border:1px solid var(--line); border-radius:999px; padding:.48rem .76rem; font-size:.76rem;
    font-weight:650; letter-spacing:.03em;
}
.sodif-trust-chip span {
    width:7px; height:7px; border-radius:50%; background:#20a67e;
    box-shadow:0 0 0 4px #dcf5ec;
}
div[data-testid="stRadio"] > div { gap:.35rem; }
div[data-testid="stRadio"] label {
    background:transparent; border-radius:8px; padding:.35rem .68rem; color:#64748b;
    font-size:.84rem; font-weight:650;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background:#e6f2f3; color:var(--teal-dark);
}
div[data-testid="stRadio"] label > div:first-child { display:none; }
.sodif-nav-rule { height:1px; background:var(--line); margin:.25rem 0 3.4rem; }
.sodif-hero { max-width:930px; padding:.4rem 0 1.6rem; }
.sodif-eyebrow, .sodif-section-label, .sodif-summary-kicker, .sodif-card-caption {
    color:var(--teal); font-size:.74rem; font-weight:800; letter-spacing:.14em;
    text-transform:uppercase;
}
.sodif-hero h1, .sodif-page-title {
    color:var(--navy); font-size:clamp(2.55rem, 5vw, 4.55rem); line-height:1.02;
    letter-spacing:-.045em; max-width:930px; margin:.72rem 0 1.2rem;
}
.sodif-lead, .sodif-page-lead {
    color:#53667d; font-size:1.18rem; line-height:1.68; max-width:790px; margin:0;
}
.sodif-promise { color:#52657b; font-weight:650; margin:0 0 0 .75rem; }
div[data-testid="stButton"] button[kind="primary"] {
    border:none; border-radius:9px; min-height:2.85rem; font-weight:750; background:var(--teal);
    box-shadow:0 10px 24px rgba(8,127,140,.19); transition:all .2s ease;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background:var(--teal-dark); transform:translateY(-1px);
}
.sodif-section-label { margin:3.8rem 0 1rem; }
.sodif-chain-card, .sodif-use-card, .sodif-capability,
.sodif-control-card, .sodif-decision-card {
    height:100%; background:rgba(255,255,255,.88); border:1px solid var(--line);
    border-radius:14px; box-shadow:0 8px 26px rgba(20,42,70,.045);
}
.sodif-chain-card { min-height:190px; padding:1.25rem; }
.sodif-card-signal { height:3px; width:34px; background:#d9e9eb; margin-bottom:2rem; }
.sodif-card-signal span { display:block; height:3px; width:15px; background:var(--teal); }
.sodif-chain-card h3, .sodif-use-card h3 {
    color:var(--navy); font-size:1rem; margin:0 0 .65rem;
}
.sodif-chain-card p, .sodif-use-card p {
    color:var(--muted); font-size:.87rem; line-height:1.55; margin:0;
}
.sodif-value-panel {
    display:grid; grid-template-columns:1.15fr .85fr; gap:4rem; align-items:center;
    margin:4.5rem 0 0; padding:2.7rem 3rem;
    background:linear-gradient(135deg,#0b1d35,#123451); border-radius:20px;
    box-shadow:0 22px 50px rgba(11,29,53,.17);
}
.sodif-section-label.light { color:#6ed3d4; margin:0 0 1rem; }
.sodif-value-panel h2 {
    color:white; font-size:2rem; letter-spacing:-.025em; margin:0 0 1rem;
}
.sodif-value-panel > div > p { color:#b9c7d8; line-height:1.65; margin:0; }
.sodif-protection-list { display:grid; gap:.7rem; }
.sodif-protection-list > div {
    display:flex; gap:.8rem; align-items:flex-start; padding:.7rem 0;
    border-bottom:1px solid rgba(255,255,255,.1);
}
.sodif-protection-list span {
    display:grid; place-items:center; width:22px; height:22px; flex:0 0 22px;
    background:rgba(70,211,174,.15); color:#6fe2be; border-radius:50%; font-size:.7rem;
}
.sodif-protection-list p { display:grid; color:white; margin:0; font-size:.88rem; }
.sodif-protection-list small { color:#9fb2c7; margin-top:.18rem; font-size:.77rem; }
.sodif-use-card {
    min-height:125px; padding:1.25rem; border-top:3px solid rgba(8,127,140,.72);
}
.sodif-page-title { font-size:3rem; margin:.45rem 0 .7rem; }
.sodif-page-lead { font-size:1rem; }
.sodif-ready-panel {
    display:flex; align-items:center; gap:1.5rem; margin:2.6rem 0 1rem; padding:2rem;
    background:white; border:1px solid var(--line); border-radius:16px;
}
.sodif-ready-mark {
    display:grid; place-items:center; width:58px; height:58px; flex:0 0 58px;
    color:var(--teal); background:#e7f4f4; border-radius:16px; font-size:1.55rem;
}
.sodif-ready-panel h2 { margin:0 0 .35rem; color:var(--navy); font-size:1.35rem; }
.sodif-ready-panel p {
    margin:0; color:var(--muted); line-height:1.55; max-width:760px;
}
.sodif-capability { display:grid; min-height:92px; padding:1rem 1.1rem; }
.sodif-capability b { color:var(--navy); font-size:.88rem; }
.sodif-capability span {
    color:var(--muted); font-size:.8rem; line-height:1.45; margin-top:.35rem;
}
.sodif-flight-summary {
    display:flex; gap:1rem; align-items:center; margin:2.5rem 0 0; padding:1.45rem 1.6rem;
    border-radius:15px; background:#eaf7f3; border:1px solid #bfe4d8;
}
.sodif-summary-icon {
    display:grid; place-items:center; width:38px; height:38px; flex:0 0 38px;
    border-radius:50%; background:var(--success); color:white; font-weight:800;
}
.sodif-flight-summary h2 { color:#075e50; font-size:1.08rem; margin:.22rem 0; }
.sodif-flight-summary p { color:#477067; font-size:.86rem; margin:0; }
.sodif-export-panel {
    display:flex; justify-content:space-between; align-items:center; gap:2rem; margin:1rem 0 .55rem;
    padding:1.35rem 1.5rem; background:white; border:1px solid var(--line); border-radius:15px;
}
.sodif-export-panel h2 { color:var(--navy); font-size:1.05rem; margin:.32rem 0 .3rem; }
.sodif-export-panel p {
    color:var(--muted); font-size:.8rem; line-height:1.45; margin:0; max-width:710px;
}
.sodif-bundle-digest { display:grid; gap:.3rem; min-width:240px; text-align:right; }
.sodif-bundle-digest small {
    color:#718197; font-size:.66rem; text-transform:uppercase; letter-spacing:.08em;
}
.sodif-bundle-digest code {
    color:#173854; background:#edf4f6; border-radius:5px; padding:.32rem .45rem;
    font-size:.67rem;
}
div[data-testid="stDownloadButton"] button {
    width:100%; min-height:2.55rem; border:1px solid #ccd8e2; border-radius:9px;
    background:white; color:var(--navy); font-weight:700;
}
div[data-testid="stDownloadButton"] button:hover {
    border-color:var(--teal); color:var(--teal-dark);
}
div[data-testid="stDownloadButton"] button[kind="primary"] {
    color:white; background:var(--teal); border-color:var(--teal);
}
.sodif-scenario-head {
    display:flex; justify-content:space-between; gap:2rem; align-items:flex-start;
    background:white; border:1px solid var(--line); border-radius:16px;
    padding:1.55rem 1.7rem; margin:.55rem 0 1rem;
}
.sodif-scenario-kicker {
    color:var(--teal); text-transform:uppercase; letter-spacing:.11em;
    font-weight:800; font-size:.69rem;
}
.sodif-scenario-head h2 {
    color:var(--navy); font-size:1.45rem; margin:.35rem 0 .4rem;
}
.sodif-scenario-head p { color:var(--muted); font-size:.88rem; margin:0; }
.sodif-verdict {
    min-width:142px; padding:.72rem .9rem; border-radius:10px; display:grid; text-align:right;
}
.sodif-verdict small {
    font-size:.66rem; text-transform:uppercase; letter-spacing:.09em; opacity:.72;
}
.sodif-verdict b { margin-top:.17rem; font-size:.93rem; }
.sodif-verdict.success { background:#e8f6f1; color:var(--success); }
.sodif-verdict.warning { background:#fff5df; color:var(--warning); }
.sodif-verdict.danger { background:#fff0f1; color:var(--danger); }
.sodif-control-card {
    min-height:130px; padding:1.05rem 1.15rem; border-top:3px solid #cbd5e1;
}
.sodif-control-card.success { border-top-color:var(--success); }
.sodif-control-card.warning { border-top-color:var(--warning); }
.sodif-control-card.danger { border-top-color:var(--danger); }
.sodif-control-card > div {
    display:flex; align-items:center; gap:.45rem; color:#728197; text-transform:uppercase;
    letter-spacing:.08em; font-size:.66rem; font-weight:750;
}
.sodif-control-card > div span {
    width:7px; height:7px; border-radius:50%; background:#94a3b8;
}
.sodif-control-card.success > div span { background:var(--success); }
.sodif-control-card.warning > div span { background:var(--warning); }
.sodif-control-card.danger > div span { background:var(--danger); }
.sodif-control-card h3 { color:var(--navy); font-size:1rem; margin:.75rem 0 .4rem; }
.sodif-control-card p {
    color:var(--muted); font-size:.78rem; line-height:1.4; margin:0;
}
.sodif-decision-card { min-height:155px; margin-top:1rem; padding:1.25rem 1.35rem; }
.sodif-decision-card.accent { background:#eef7f8; border-color:#c8e1e4; }
.sodif-decision-card h3 {
    color:var(--navy); font-size:1rem; line-height:1.45; margin:.75rem 0 .5rem;
}
.sodif-decision-card p {
    color:var(--muted); font-size:.8rem; line-height:1.5; margin:0;
}
.sodif-subsection-title {
    color:var(--navy); font-weight:800; font-size:.86rem; margin:2.1rem 0 .8rem;
}
.sodif-timeline, .sodif-evidence {
    background:white; border:1px solid var(--line); border-radius:14px; padding:1rem 1.15rem;
}
.sodif-timeline-item {
    position:relative; display:flex; gap:.75rem; padding:.38rem 0 .78rem;
}
.sodif-timeline-item:not(:last-child)::before {
    content:""; position:absolute; left:4px; top:15px; bottom:-3px;
    width:1px; background:#d3e1e4;
}
.sodif-timeline-item > span {
    width:9px; height:9px; flex:0 0 9px; margin-top:.3rem; border-radius:50%;
    background:var(--teal); box-shadow:0 0 0 4px #e4f3f3; z-index:1;
}
.sodif-timeline-item p {
    color:#52657b; font-size:.79rem; line-height:1.45; margin:0;
}
.sodif-evidence-row {
    display:flex; justify-content:space-between; align-items:center; gap:1rem;
    padding:.65rem 0; border-bottom:1px solid #edf1f5;
}
.sodif-evidence-row:last-child { border-bottom:none; }
.sodif-evidence-row span { color:#64748b; font-size:.74rem; }
.sodif-evidence-row code {
    color:#173854; background:#edf4f6; border-radius:5px; padding:.26rem .42rem;
    font-size:.69rem;
}
div[data-testid="stSelectbox"] label {
    color:#53667d; font-size:.78rem; font-weight:700;
}
div[data-testid="stSelectbox"] > div > div {
    background:white; border-color:var(--line);
}
@media (max-width: 800px) {
    .block-container { padding:1.2rem 1.1rem 3rem; }
    .sodif-trust-chip { display:none; }
    .sodif-nav-rule { margin-bottom:2.2rem; }
    .sodif-value-panel { grid-template-columns:1fr; gap:2rem; padding:2rem 1.4rem; }
    .sodif-export-panel { display:grid; }
    .sodif-bundle-digest { min-width:0; text-align:left; }
    .sodif-scenario-head { display:grid; }
    .sodif-verdict { text-align:left; }
}
</style>
"""
