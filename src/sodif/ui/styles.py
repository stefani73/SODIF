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
header[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"], #MainMenu, footer { display:none; }
.block-container { max-width:1220px; padding:1.5rem 2.5rem 5rem; }
section[data-testid="stSidebar"] { border-right:1px solid #173652; }
section[data-testid="stSidebar"] > div { background:var(--navy); }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    padding-top:.35rem; border-top:1px solid rgba(255,255,255,.1);
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {
    color:#7f93aa; font-size:.68rem; letter-spacing:.11em; text-transform:uppercase;
}
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"],
section[data-testid="stSidebar"] [data-testid="stNavSectionHeader"] * {
    color:#8297ad !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    color:#bdcada; border-radius:9px; margin:.12rem 0;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] * {
    color:inherit !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
    color:white; background:rgba(255,255,255,.07);
}
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    color:white; background:rgba(61,197,193,.16);
}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] * {
    color:#bdcada !important;
}
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sodif-sidebar-brand) {
    position:static;
}
.sodif-sidebar-brand {
    position:absolute; z-index:2; top:1.05rem; left:1.2rem;
    display:flex; align-items:center; gap:.8rem;
}
.sodif-sidebar-brand .sodif-mark {
    background:rgba(255,255,255,.08); border-color:rgba(100,220,215,.28); box-shadow:none;
}
.sodif-sidebar-brand > div { display:grid; }
.sodif-sidebar-brand strong { color:white; font-size:1rem; letter-spacing:.14em; }
.sodif-sidebar-brand small { color:#8297ad; font-size:.66rem; margin-top:.18rem; }
.sodif-sidebar-footer {
    display:flex; align-items:flex-start; gap:.7rem; margin-top:1.8rem; padding:1rem .85rem;
    border:1px solid rgba(255,255,255,.09); border-radius:11px; background:rgba(255,255,255,.035);
}
.sodif-sidebar-footer > span {
    width:8px; height:8px; flex:0 0 8px; margin-top:.25rem; border-radius:50%;
    background:#41c59f; box-shadow:0 0 0 4px rgba(65,197,159,.12);
}
.sodif-sidebar-footer div { display:grid; }
.sodif-sidebar-footer strong { color:#dbe6f0; font-size:.72rem; }
.sodif-sidebar-footer small { color:#7f93aa; font-size:.66rem; line-height:1.4; margin-top:.2rem; }
.sodif-header {
    display:flex; align-items:center; justify-content:space-between; margin-bottom:3.2rem;
    padding-bottom:1rem; border-bottom:1px solid var(--line);
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
.sodif-context {
    color:#728197; font-size:.72rem; border-left:1px solid #d6e0e8; padding-left:.72rem;
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
.st-key-overview_architecture_link a, .st-key-security_demo_link a,
.st-key-empty_control_link a, .st-key-reports_shortcut a {
    min-height:2.75rem; border-radius:9px; border:1px solid var(--teal); font-weight:750;
    color:white; background:var(--teal); box-shadow:0 9px 22px rgba(8,127,140,.16);
}
.st-key-overview_architecture_link a:hover, .st-key-security_demo_link a:hover,
.st-key-empty_control_link a:hover, .st-key-reports_shortcut a:hover {
    color:white; background:var(--teal-dark); border-color:var(--teal-dark);
}
.st-key-overview_architecture_link a *, .st-key-security_demo_link a *,
.st-key-empty_control_link a *, .st-key-reports_shortcut a * { color:white !important; }
div[data-testid="stButton"] button[kind="primary"] {
    border:none; border-radius:9px; min-height:2.85rem; font-weight:750; background:var(--teal);
    box-shadow:0 10px 24px rgba(8,127,140,.19); transition:all .2s ease;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background:var(--teal-dark); transform:translateY(-1px);
}
.sodif-section-label { margin:3.8rem 0 1rem; }
.sodif-section-label.compact { margin-top:2.5rem; }
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
.sodif-module-card, .sodif-architecture-card {
    height:100%; background:rgba(255,255,255,.92); border:1px solid var(--line);
    border-radius:16px; box-shadow:0 10px 30px rgba(20,42,70,.05); overflow:hidden;
}
.sodif-module-card {
    position:relative; min-height:226px; padding:1.35rem 1.35rem 1.5rem;
    border-top:4px solid var(--teal);
}
.sodif-module-card.module-archive, .sodif-architecture-card.module-archive {
    border-top-color:#326da8;
}
.sodif-module-card.module-gateway, .sodif-architecture-card.module-gateway {
    border-top-color:#7957a8;
}
.sodif-module-card-head { display:flex; justify-content:space-between; align-items:center; }
.sodif-module-card-head span {
    display:grid; place-items:center; width:32px; height:32px; color:var(--teal-dark);
    background:#e7f4f4; border-radius:9px; font-size:.7rem; font-weight:850;
}
.sodif-module-card-head small {
    color:#8794a4; font-size:.61rem; font-weight:750; letter-spacing:.09em;
    text-transform:uppercase;
}
.sodif-module-card h2 {
    color:var(--navy); font-size:1.15rem; line-height:1.28; margin:1.4rem 0 .65rem;
}
.sodif-module-card p {
    color:var(--muted); font-size:.81rem; line-height:1.58; margin:0;
}
.sodif-module-contract {
    display:grid; grid-template-columns:1fr 1.4fr 1fr; gap:1px; margin:2.2rem 0 .5rem;
    overflow:hidden; background:#d6e1e8; border:1px solid #d6e1e8; border-radius:15px;
}
.sodif-module-contract > div { min-height:142px; padding:1.25rem; background:#fff; }
.sodif-module-contract > div.active { background:#edf7f7; }
.sodif-module-contract small {
    color:#718197; font-size:.64rem; font-weight:850; letter-spacing:.11em;
    text-transform:uppercase;
}
.sodif-module-contract .active small { color:var(--teal-dark); }
.sodif-module-contract p {
    color:#4f6278; font-size:.81rem; line-height:1.55; margin:.7rem 0 0;
}
.sodif-module-value { margin-top:3.4rem; }
.sodif-architecture-card {
    min-height:335px; padding:1.35rem; border-top:4px solid var(--teal);
}
.sodif-architecture-card > small {
    color:var(--teal-dark); font-size:.64rem; font-weight:850; letter-spacing:.08em;
    text-transform:uppercase;
}
.sodif-architecture-card h2 {
    color:var(--navy); min-height:55px; font-size:1.12rem; line-height:1.35;
    margin:1rem 0 .7rem;
}
.sodif-architecture-card p {
    min-height:112px; color:var(--muted); font-size:.8rem; line-height:1.58; margin:0;
}
.sodif-architecture-card footer {
    display:grid; gap:.35rem; margin-top:1rem; padding-top:.9rem; border-top:1px solid #e5ebf0;
}
.sodif-architecture-card footer b {
    color:#718197; font-size:.6rem; letter-spacing:.1em; text-transform:uppercase;
}
.sodif-architecture-card footer span { color:#41576f; font-size:.72rem; line-height:1.45; }
.sodif-platform-flow, .sodif-gateway-flow {
    display:grid; align-items:stretch; margin:1rem 0 0; padding:1.15rem;
    background:#fff; border:1px solid var(--line); border-radius:16px;
}
.sodif-gateway-route {
    min-height:258px; padding:1.4rem; background:linear-gradient(150deg,#0d223c,#153d59);
    border-radius:16px; box-shadow:0 16px 36px rgba(11,29,53,.14);
}
.sodif-gateway-route > small {
    color:#70d1d1; font-size:.63rem; font-weight:850; letter-spacing:.11em;
    text-transform:uppercase;
}
.sodif-gateway-route h2 {
    color:#fff; font-size:1.25rem; line-height:1.35; margin:.7rem 0 1.2rem;
}
.sodif-gateway-route > div {
    display:flex; justify-content:space-between; gap:1rem; padding:.72rem 0;
    border-top:1px solid rgba(255,255,255,.1);
}
.sodif-gateway-route span { color:#8ea5ba; font-size:.69rem; }
.sodif-gateway-route strong {
    color:#d9e7ef; font-size:.69rem; font-weight:700; text-align:right;
}
.sodif-gateway-scenario {
    min-height:52px; color:var(--muted); font-size:.79rem; line-height:1.55;
    margin:.8rem 0 1rem;
}
.sodif-gateway-ready {
    display:flex; align-items:center; gap:1rem; margin:1rem 0 0; padding:1.2rem 1.35rem;
    background:#fff; border:1px solid var(--line); border-radius:14px;
}
.sodif-gateway-ready > span {
    width:11px; height:11px; flex:0 0 11px; border-radius:50%; background:var(--teal);
    box-shadow:0 0 0 6px #e3f2f3;
}
.sodif-gateway-ready div { display:grid; gap:.15rem; }
.sodif-gateway-ready small {
    color:var(--teal-dark); font-size:.59rem; font-weight:850; letter-spacing:.1em;
    text-transform:uppercase;
}
.sodif-gateway-ready h2 { color:var(--navy); font-size:.94rem; margin:0; }
.sodif-gateway-ready p { color:var(--muted); font-size:.72rem; margin:0; }
.sodif-gateway-decision {
    margin:1.1rem 0 .75rem; overflow:hidden; background:#fff; border:1px solid var(--line);
    border-radius:16px; box-shadow:0 10px 28px rgba(20,42,70,.045);
}
.sodif-gateway-decision.success { border-color:#b9ddd2; }
.sodif-gateway-decision.danger { border-color:#efc9cd; }
.sodif-gateway-decision-head { display:flex; gap:1rem; padding:1.35rem 1.45rem; }
.sodif-gateway-decision-head > span {
    width:12px; height:12px; flex:0 0 12px; margin-top:.35rem; border-radius:50%;
    background:var(--success); box-shadow:0 0 0 6px #e2f2ed;
}
.sodif-gateway-decision.danger .sodif-gateway-decision-head > span {
    background:var(--danger); box-shadow:0 0 0 6px #fae9eb;
}
.sodif-gateway-decision-head small {
    color:#718197; font-size:.6rem; font-weight:850; letter-spacing:.1em; text-transform:uppercase;
}
.sodif-gateway-decision-head h2 {
    color:var(--navy); font-size:1.2rem; margin:.24rem 0 .35rem;
}
.sodif-gateway-decision-head p { color:var(--muted); font-size:.79rem; margin:0; }
.sodif-gateway-decision-meta {
    display:grid; grid-template-columns:1fr 1fr .85fr 1.15fr; gap:1px;
    background:#dce5eb; border-top:1px solid #dce5eb;
}
.sodif-gateway-decision-meta > div {
    display:grid; gap:.25rem; padding:.85rem 1rem; background:#f7f9fb;
}
.sodif-gateway-decision-meta small {
    color:#7b8999; font-size:.57rem; font-weight:800; letter-spacing:.08em;
    text-transform:uppercase;
}
.sodif-gateway-decision-meta strong {
    color:#29445e; font-size:.68rem; overflow-wrap:anywhere;
}
.sodif-gateway-check {
    display:flex; align-items:flex-start; gap:.7rem; margin:.42rem 0; padding:.78rem 1rem;
    background:#fff; border:1px solid var(--line); border-radius:11px;
}
.sodif-gateway-check > span {
    width:9px; height:9px; flex:0 0 9px; margin-top:.3rem; border-radius:50%;
    background:var(--success); box-shadow:0 0 0 4px #e5f3ef;
}
.sodif-gateway-check.failed > span { background:var(--danger); box-shadow:0 0 0 4px #faeaec; }
.sodif-gateway-check p { display:grid; gap:.15rem; margin:0; }
.sodif-gateway-check strong { color:var(--navy); font-size:.75rem; }
.sodif-gateway-check small { color:var(--muted); font-size:.67rem; line-height:1.4; }
.sodif-platform-flow { grid-template-columns:1fr 34px 1fr 34px 1fr 34px 1fr; }
.sodif-gateway-flow { grid-template-columns:1fr 42px 1.25fr 42px 1fr; margin-top:3.2rem; }
.sodif-platform-flow > div, .sodif-gateway-flow > div {
    display:grid; align-content:center; gap:.28rem; min-height:94px; padding:1rem;
    background:#f7f9fb; border-radius:11px;
}
.sodif-gateway-flow > div.active { background:#eaf6f6; border:1px solid #cde5e5; }
.sodif-platform-flow small, .sodif-gateway-flow small {
    color:#718197; font-size:.6rem; font-weight:850; letter-spacing:.09em; text-transform:uppercase;
}
.sodif-platform-flow strong, .sodif-gateway-flow strong {
    color:var(--navy); font-size:.82rem;
}
.sodif-gateway-flow span { color:var(--muted); font-size:.68rem; line-height:1.4; }
.sodif-platform-flow > i, .sodif-gateway-flow > i { position:relative; }
.sodif-platform-flow > i::before, .sodif-gateway-flow > i::before {
    content:""; position:absolute; top:50%; left:7px; right:7px; height:1px; background:#9db5c5;
}
.sodif-platform-flow > i::after, .sodif-gateway-flow > i::after {
    content:""; position:absolute; top:calc(50% - 3px); right:7px; width:6px; height:6px;
    border-top:1px solid #7e9aab; border-right:1px solid #7e9aab; transform:rotate(45deg);
}
.sodif-page-title { font-size:3rem; margin:.45rem 0 .7rem; }
.sodif-page-lead { font-size:1rem; }
.sodif-page-intro { max-width:850px; }
.sodif-inline-note { color:#728197; font-size:.77rem; margin:.85rem 0 0 .5rem; }
.sodif-ready-panel {
    display:flex; align-items:center; gap:1.5rem; margin:2.6rem 0 1rem; padding:2rem;
    background:white; border:1px solid var(--line); border-radius:16px;
}
.sodif-ready-mark {
    display:grid; place-items:center; width:58px; height:58px; flex:0 0 58px;
    background:#e7f4f4; border-radius:16px;
}
.sodif-ready-mark span {
    width:18px; height:18px; border:3px solid var(--teal); border-radius:6px;
    transform:rotate(45deg); box-shadow:inset 0 0 0 3px #e7f4f4;
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
.sodif-summary-icon::after {
    content:""; width:11px; height:6px; border-left:2px solid white;
    border-bottom:2px solid white; transform:rotate(-45deg) translate(1px,-1px);
}
.sodif-flight-summary h2 { color:#075e50; font-size:1.08rem; margin:.22rem 0; }
.sodif-flight-summary p { color:#477067; font-size:.86rem; margin:0; }
.sodif-export-panel {
    display:flex; justify-content:space-between; align-items:center; gap:2rem; margin:1rem 0 .55rem;
    padding:1.35rem 1.5rem; background:white; border:1px solid var(--line); border-radius:15px;
}
.sodif-report-identity {
    display:grid; grid-template-columns:1.15fr .8fr 1fr .75fr; gap:1rem; margin:1rem 0;
    padding:1rem 1.2rem; background:#eef4f7; border:1px solid #d6e2e9; border-radius:13px;
}
.sodif-report-identity > div { display:grid; gap:.25rem; }
.sodif-report-identity small {
    color:#728197; font-size:.64rem; letter-spacing:.08em; text-transform:uppercase;
}
.sodif-report-identity strong, .sodif-report-identity code {
    color:#173854; font-size:.76rem; font-weight:700; background:transparent; padding:0;
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
.sodif-feature-panel {
    min-height:205px; padding:1.65rem 1.75rem; background:white; border:1px solid var(--line);
    border-radius:16px; box-shadow:0 8px 26px rgba(20,42,70,.04);
}
.sodif-feature-panel.accent { background:#eef7f8; border-color:#c8e1e4; }
.sodif-feature-panel h2 {
    color:var(--navy); font-size:1.25rem; line-height:1.35; margin:.8rem 0 .65rem;
}
.sodif-feature-panel p { color:var(--muted); font-size:.86rem; line-height:1.58; margin:0; }
.sodif-boundary-panel {
    display:grid; grid-template-columns:.85fr 1.15fr; gap:3rem; align-items:center;
    margin:1rem 0 1.2rem; padding:1.8rem 2rem; background:linear-gradient(135deg,#0b1d35,#123451);
    border-radius:16px;
}
.sodif-boundary-panel h2 { color:white; font-size:1.35rem; margin:.7rem 0 0; }
.sodif-boundary-panel p { color:#b9c7d8; font-size:.86rem; line-height:1.6; margin:0; }
.sodif-empty-panel {
    display:flex; align-items:center; gap:1.5rem; margin:2.4rem 0 1rem; padding:2rem;
    background:white; border:1px solid var(--line); border-radius:16px;
}
.sodif-empty-panel h2 { color:var(--navy); font-size:1.25rem; margin:0 0 .35rem; }
.sodif-ingestion-sample {
    display:flex; align-items:center; justify-content:space-between; margin:2.4rem 0 1rem;
    padding:1.55rem 1.7rem; background:linear-gradient(135deg,#0e2944,#123d59);
    border-radius:16px; box-shadow:0 16px 35px rgba(11,29,53,.13);
}
.sodif-ingestion-sample h2 { color:white; font-size:1.25rem; margin:.35rem 0 .35rem; }
.sodif-ingestion-sample p { color:#b9c9d9; margin:0; line-height:1.55; }
.sodif-ingestion-receipt {
    display:flex; align-items:center; gap:1.3rem; margin:2.2rem 0 1rem; padding:1.55rem;
    background:#eaf7f3; border:1px solid #bfe4d8; border-radius:15px;
}
.sodif-ingestion-receipt h2 { color:#126b58; font-size:1.25rem; margin:.25rem 0 .3rem; }
.sodif-ingestion-receipt p { color:#4c6f67; margin:0; }
.sodif-ingestion-metadata {
    display:grid; grid-template-columns:1.1fr .55fr 1fr 1.35fr 1.4fr; gap:1px;
    overflow:hidden; background:var(--line); border:1px solid var(--line); border-radius:13px;
}
.sodif-ingestion-metadata > div { display:grid; gap:.4rem; padding:1rem; background:#fff; }
.sodif-ingestion-metadata small {
    color:#7a8899; font-size:.63rem; font-weight:750; letter-spacing:.09em;
    text-transform:uppercase;
}
.sodif-ingestion-metadata strong, .sodif-ingestion-metadata code {
    color:var(--navy); font-size:.76rem; overflow-wrap:anywhere;
}
.sodif-registry-stat {
    display:grid; min-height:116px; padding:1.05rem 1.15rem; background:#fff;
    border:1px solid var(--line); border-radius:14px; box-shadow:0 8px 24px rgba(20,42,70,.035);
}
.sodif-registry-stat small {
    color:#748399; font-size:.63rem; font-weight:800; letter-spacing:.09em;
    text-transform:uppercase;
}
.sodif-registry-stat strong { color:var(--navy); font-size:1.65rem; margin:.28rem 0 .08rem; }
.sodif-registry-stat span { color:var(--muted); font-size:.73rem; }
.sodif-registry-results-head {
    display:flex; align-items:center; justify-content:space-between; margin:.2rem 0 .8rem;
}
.sodif-registry-results-head strong { color:var(--navy); font-size:.87rem; }
.sodif-registry-results-head span { color:#7a8899; font-size:.7rem; }
.sodif-registry-record {
    margin-top:.7rem; padding:1rem 1.05rem; background:#fff; border:1px solid var(--line);
    border-radius:13px 13px 6px 6px; transition:border-color .18s, box-shadow .18s;
}
.sodif-registry-record.active {
    border-color:#8ec8ce; box-shadow:0 8px 24px rgba(18,139,148,.09);
}
.sodif-registry-record > div { display:flex; align-items:center; justify-content:space-between; }
.sodif-registry-record > div span {
    padding:.22rem .42rem; color:#0d7780; background:#e7f4f4; border-radius:5px;
    font-size:.6rem; font-weight:850; letter-spacing:.08em;
}
.sodif-registry-record small { color:#7b899a; font-size:.67rem; }
.sodif-registry-record h3 {
    color:var(--navy); font-size:.92rem; line-height:1.35; margin:.75rem 0 .28rem;
}
.sodif-registry-record p { color:#64748b; font-size:.72rem; margin:0; }
.sodif-registry-record footer {
    display:flex; justify-content:space-between; gap:.7rem; margin-top:.8rem; padding-top:.65rem;
    border-top:1px solid #edf1f5; color:#758497; font-size:.66rem;
}
div[class*="st-key-registry-open-"] button { margin-top:-.2rem; border-radius:0 0 9px 9px; }
.sodif-registry-detail-head { padding:.15rem 0 .5rem; }
.sodif-registry-detail-head h2 { color:var(--navy); font-size:1.45rem; margin:.5rem 0 .25rem; }
.sodif-registry-detail-head p { color:var(--muted); margin:0; font-size:.8rem; }
.sodif-assurance-label {
    display:flex; align-items:center; gap:.42rem; color:#167460; font-size:.65rem;
    font-weight:800; letter-spacing:.07em; text-transform:uppercase;
}
.sodif-assurance-label span { width:7px; height:7px; border-radius:50%; background:#23b58d; }
.sodif-registry-metadata {
    display:grid; grid-template-columns:1fr 1.15fr .65fr 1.35fr; gap:1px; margin:.8rem 0 1rem;
    overflow:hidden; background:var(--line); border:1px solid var(--line); border-radius:12px;
}
.sodif-registry-metadata > div { display:grid; gap:.32rem; padding:.85rem; background:#fff; }
.sodif-registry-metadata small {
    color:#7a8899; font-size:.59rem; font-weight:800; letter-spacing:.08em;
    text-transform:uppercase;
}
.sodif-registry-metadata strong, .sodif-registry-metadata code {
    color:var(--navy); font-size:.71rem; overflow-wrap:anywhere;
}
.sodif-preview-label {
    color:#607187; font-size:.68rem; font-weight:750; margin:.25rem 0 .65rem;
}
.sodif-traceability-intro {
    display:flex; justify-content:space-between; gap:1rem; padding:.6rem 0 .9rem;
    color:var(--navy); font-size:.78rem;
}
.sodif-traceability-intro span { color:var(--muted); font-size:.7rem; }
.sodif-revision-history {
    padding:.4rem 1rem; background:#fff; border:1px solid var(--line); border-radius:13px;
}
.sodif-revision-item {
    position:relative; display:grid; grid-template-columns:12px 1fr auto; gap:.7rem;
    align-items:center; padding:.8rem 0;
}
.sodif-revision-item:not(:last-child) { border-bottom:1px solid #edf1f5; }
.sodif-revision-item > span { width:8px; height:8px; border-radius:50%; background:#bdc9d5; }
.sodif-revision-item.active > span { background:var(--teal); box-shadow:0 0 0 4px #e4f3f3; }
.sodif-revision-item div { display:grid; gap:.15rem; }
.sodif-revision-item strong { color:var(--navy); font-size:.78rem; }
.sodif-revision-item small, .sodif-revision-item time { color:#748399; font-size:.65rem; }
.sodif-package-proof {
    display:grid; grid-template-columns:.8fr 1.2fr; gap:1rem; margin-top:.8rem; padding:.85rem 1rem;
    background:#eef7f5; border:1px solid #d4eae5; border-radius:11px;
}
.sodif-package-proof > div { display:grid; gap:.25rem; }
.sodif-package-proof small {
    color:#6c7f8f; font-size:.59rem; font-weight:800; letter-spacing:.06em;
    text-transform:uppercase;
}
.sodif-package-proof code { color:#145a50; font-size:.68rem; background:transparent; padding:0; }
section[data-testid="stFileUploaderDropzone"] button div[data-testid="stMarkdownContainer"] p {
    display:none !important;
}
section[data-testid="stFileUploaderDropzone"] button div[data-testid="stMarkdownContainer"]::after {
    content:"Selectează"; color:var(--navy); font-size:.8rem !important;
}
div[data-testid="stFileUploaderDropzoneInstructions"] span { font-size:0; }
div[data-testid="stFileUploaderDropzoneInstructions"] span::after {
    content:"Până la 200 MB"; font-size:.74rem;
}
.sodif-empty-panel p { color:var(--muted); line-height:1.55; margin:0; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    height:100%; background:rgba(255,255,255,.88); border-color:var(--line); border-radius:14px;
    box-shadow:0 8px 24px rgba(20,42,70,.035);
}
div[data-testid="stVerticalBlockBorderWrapper"] h4 {
    color:var(--navy); font-size:.92rem; line-height:1.35; margin-bottom:.5rem;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stCaptionContainer"] {
    color:var(--muted); font-size:.76rem; line-height:1.45;
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
.sodif-comparison-grid {
    display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.8rem;
}
.sodif-comparison-card {
    background:white; border:1px solid var(--line); border-top:3px solid var(--teal);
    border-radius:14px; padding:1rem 1.05rem;
}
.sodif-comparison-card.warning { border-top-color:#b7791f; }
.sodif-comparison-card small {
    color:#718096; font-size:.65rem; font-weight:800; letter-spacing:.06em;
    text-transform:uppercase;
}
.sodif-comparison-card h3 { color:var(--navy); font-size:.94rem; margin:.3rem 0 .55rem; }
.sodif-comparison-card ul { list-style:none; padding:0; margin:0 0 .7rem; }
.sodif-comparison-card li {
    color:#52657b; font-size:.73rem; padding:.24rem 0; border-bottom:1px solid #edf1f5;
}
.sodif-comparison-card strong { color:#087a64; font-size:.72rem; }
.sodif-comparison-card.warning strong { color:#9a620b; }
.sodif-data-path {
    display:flex; align-items:center; gap:.5rem; margin:1rem 0 .35rem;
}
.sodif-data-path span {
    color:#29425c; background:#edf4f6; border-radius:999px; padding:.35rem .62rem;
    font-size:.67rem; font-weight:750; white-space:nowrap;
}
.sodif-data-path i { flex:1; height:1px; background:#c8d8df; min-width:12px; }
div[data-testid="stSelectbox"] label {
    color:#53667d; font-size:.78rem; font-weight:700;
}
div[data-testid="stSelectbox"] > div > div {
    background:white; border-color:var(--line);
}
.sodif-flight-choice { min-height:8.4rem; padding:.25rem .2rem .1rem; }
.sodif-flight-choice h2 { color:var(--navy); font-size:1.28rem; margin:.55rem 0 .35rem; }
.sodif-flight-choice p { color:var(--muted); font-size:.78rem; line-height:1.55; margin:0; }
.sodif-flight-active {
    display:inline-flex; align-items:center; gap:.7rem; margin:1.8rem 0 .75rem;
    padding:.45rem .72rem; background:#edf7f5; border:1px solid #d0e9e3; border-radius:999px;
}
.sodif-flight-active strong { color:#0c6e5b; font-size:.73rem; }
.sodif-flight-active span { color:#5d7181; font-size:.67rem; }
@media (max-width: 800px) {
    .block-container { padding:1.2rem 1.1rem 3rem; }
    .sodif-trust-chip { display:none; }
    .sodif-context { display:none; }
    .sodif-header { margin-bottom:2.2rem; }
    .sodif-value-panel { grid-template-columns:1fr; gap:2rem; padding:2rem 1.4rem; }
    .sodif-module-contract { grid-template-columns:1fr; }
    .sodif-platform-flow, .sodif-gateway-flow { grid-template-columns:1fr; }
    .sodif-gateway-decision-meta { grid-template-columns:1fr 1fr; }
    .sodif-platform-flow > i, .sodif-gateway-flow > i { min-height:24px; }
    .sodif-platform-flow > i::before, .sodif-gateway-flow > i::before {
        top:5px; bottom:5px; left:50%; width:1px; height:auto;
    }
    .sodif-platform-flow > i::after, .sodif-gateway-flow > i::after {
        top:auto; bottom:5px; left:calc(50% - 3px); transform:rotate(135deg);
    }
    .sodif-export-panel { display:grid; }
    .sodif-bundle-digest { min-width:0; text-align:left; }
    .sodif-report-identity { grid-template-columns:1fr; }
    .sodif-boundary-panel { grid-template-columns:1fr; gap:1.2rem; }
    .sodif-ingestion-metadata { grid-template-columns:1fr; }
    .sodif-registry-metadata { grid-template-columns:1fr 1fr; }
    .sodif-traceability-intro { display:grid; }
    .sodif-scenario-head { display:grid; }
    .sodif-verdict { text-align:left; }
    .sodif-comparison-grid { grid-template-columns:1fr; }
    .sodif-data-path { display:grid; grid-template-columns:1fr; }
    .sodif-data-path i { display:none; }
}
</style>
"""
