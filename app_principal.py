
# -*- coding: utf-8 -*-
"""
app_principal.py
- Página principal com sidebar.
- Pastas: GET /roots automático + botões de ação (Scan, Indexar) por linha.
- Arquivos: tabela com botões (Abrir file://, Download, Copiar) e GET /files.
- Busca: agora em TABELA com colunas e botões (Abrir, Download, Copiar).
- Status: GET /health.
- Tudo com addEventListener e construção de DOM (sem template literals nas linhas).
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/app", tags=["App UI"])

@router.get("/principal", response_class=HTMLResponse)
def render_principal():
    html = r"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Doc Index • Principal</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { --bg:#0f172a; --panel:#111827; --border:#1f2937; --text:#e5e7eb; --muted:#94a3b8; --ok:#22c55e; --warn:#f59e0b; --err:#ef4444; --info:#3b82f6; }
    * { box-sizing: border-box; }
    body { margin:0; background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial; }
    .layout { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
    .sidebar { background: #0b1220; border-right: 1px solid var(--border); padding: 16px; }
    .brand { font-weight: 600; font-size: 16px; margin-bottom: 16px; }
    .nav { display: flex; flex-direction: column; gap: 6px; }
    .nav button { text-align: left; padding: 10px 12px; border-radius: 8px; border:1px solid var(--border); background:#111827; color:#fff; cursor:pointer; font-size: 13px; }
    .nav button.active { background:#1f2937; border-color:#334155; }
    .nav button:hover { filter: brightness(1.05); }
    .content { padding: 16px; }
    .panel { background: var(--panel); border:1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 16px; }
    .section-title { font-size: 14px; color: var(--muted); margin-bottom: 10px; }
    input[type=text], select { width: 100%; padding: 10px 12px; border-radius:8px; border:1px solid var(--border); background:#0b1220; color:var(--text); }
    .row { display:flex; gap:12px; align-items:flex-end; flex-wrap: wrap; }
    .row > div { flex: 1; min-width: 220px; }
    .btn { padding: 8px 12px; border-radius:8px; border:1px solid var(--border); color:#fff; background:#1f2937; cursor:pointer; font-size: 13px; }
    .btn:hover { filter: brightness(1.08); }
    .btn-primary { background:#0b5; border-color:#0a4; }
    .btn-info { background:#1855b3; border-color:#144896; }
    .muted { color: var(--muted); }
    .results { background:#0b1220; border:1px solid var(--border); border-radius:10px; padding:12px; }
    table { width:100%; border-collapse:collapse; margin-top:8px; }
    th, td { border-bottom:1px solid var(--border); padding:8px; font-size:13px; vertical-align: top; }
    th { text-align:left; color: var(--muted); }
    code { background:#0b1220; padding:2px 6px; border-radius:6px; border:1px solid var(--border); word-break: break-all; }
    .small { font-size:12px; }
    .nowrap { white-space: nowrap; }
    .center { text-align: center; }

    /* Botões de ação nas tabelas */
    .btn-sm { padding:6px 10px; border-radius:6px; border:1px solid var(--border); background:#1f2937; color:#fff; cursor:pointer; font-size:12px; }
    .btn-sm:hover { filter:brightness(1.08); }
    .btn-open { background:#1855b3; border-color:#144896; }
    .btn-download { background:#0b5; border-color:#0a4; }
    .btn-copy { background:#64748b; border-color:#475569; }
    .btn-scan { background:#b7810a; border-color:#a97008; }
    .btn-index { background:#0b5; border-color:#0a4; }
    .actions { display:flex; gap:6px; justify-content:center; }
  </style>
</head>
<body>
<div class="layout">
  <aside class="sidebar">
    <div class="brand">Doc Index</div>
    <div class="nav">
      <button id="btnPastas" class="active">Pastas</button>
      <button id="btnArquivos">Arquivos (metadados)</button>
      <button id="btnBusca">Busca (full-text)</button>
      <button id="btnStatus">Status</button>
    </div>
    <div style="margin-top:12px; font-size:12px;" class="muted">
      <div>Versão UI: 1.0</div>
      <div>Servidor: mesma origem</div>
    </div>
  </aside>

  <main class="content">
    <!-- VIEW: PASTAS -->
    <div id="viewPastas" class="panel">
      <div class="section-title">Pastas cadastradas</div>

      <div class="row">
        <div>
          <label for="pastasExt">Extensões (scan/index)</label>
          <input id="pastasExt" type="text" value="pdf,docx,pptx,xlsx,txt,csv">
        </div>
        <div style="flex:0 0 auto;">
          <button class="btn btn-info" id="btnReloadRoots">Recarregar lista</button>
        </div>
      </div>
      <div id="pastasMsg" class="muted" style="margin-top:8px;">Carregando...</div>

      <table style="margin-top:10px;">
        <thead>
          <tr>
            <th>ID</th>
            <th>Path</th>
            <th class="muted">files_count</th>
            <th class="muted">total_size</th>
            <th class="muted">last_scan_at</th>
            <th class="center">Ações</th>
          </tr>
        </thead>
        <tbody id="pastasBody"></tbody>
      </table>
    </div>

    <!-- VIEW: ARQUIVOS -->
    <div id="viewArquivos" class="panel" style="display:none;">
      <div class="section-title">Arquivos (metadados)</div>
      <div class="row">
        <div>
          <label for="filesRootId">ID da raiz</label>
          <input id="filesRootId" type="text" placeholder="Ex.: 1">
        </div>
        <div>
          <label for="filesExt">Extensão (opcional)</label>
          <input id="filesExt" type="text" placeholder="Ex.: pdf">
        </div>
        <div>
          <label for="filesLimit">Limite</label>
          <input id="filesLimit" type="text" value="100">
        </div>
        <div style="flex:0 0 auto;">
          <button class="btn btn-info" id="btnFilesLoad">Carregar</button>
        </div>
      </div>
      <div id="filesMsg" class="muted" style="margin-top:8px;"></div>

      <div class="results" style="margin-top:10px;">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th class="nowrap">Extensão</th>
              <th class="nowrap">Tamanho</th>
              <th class="nowrap">Modificado</th>
              <th>Caminho</th>
              <th class="center">Ações</th>
            </tr>
          </thead>
          <tbody id="filesBody">
            <tr><td colspan="6" class="muted">Nenhum dado carregado.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- VIEW: BUSCA (tabela) -->
    <div id="viewBusca" class="panel" style="display:none;">
      <div class="section-title">Busca full-text</div>
      <div class="row">
        <div>
          <label for="searchRootId">ID da raiz (opcional)</label>
          <input id="searchRootId" type="text" placeholder="Ex.: 1">
        </div>
        <div>
          <label for="searchQuery">Consulta</label>
          <input id="searchQuery" type="text" placeholder='Ex.: "válvula de retenção" AND inox'>
        </div>
        <div>
          <label for="searchExt">Extensões</label>
          <input id="searchExt" type="text" value="pdf,docx,txt">
        </div>
        <div>
          <label for="searchLimit">Limite</label>
          <input id="searchLimit" type="text" value="50">
        </div>
        <div style="flex:0 0 auto;">
          <button class="btn btn-primary" id="btnSearchRun">Buscar</button>
        </div>
      </div>
      <div id="searchMsg" class="muted" style="margin-top:8px;"></div>

      <div class="results" style="margin-top:10px;">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th class="nowrap">Extensão</th>
              <th>Caminho</th>
              <th>Trecho</th>
              <th class="center">Ações</th>
            </tr>
          </thead>
          <tbody id="searchBody">
            <tr><td colspan="5" class="muted">Nenhum resultado.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- VIEW: STATUS -->
    <div id="viewStatus" class="panel" style="display:none;">
      <div class="section-title">Status do serviço</div>
      <div class="row">
        <div style="flex:0 0 auto;">
          <button class="btn btn-info" id="btnHealthCheck">Atualizar</button>
        </div>
      </div>
      <div id="healthMsg" class="muted" style="margin-top:8px;">Clique em "Atualizar".</div>
    </div>
  </main>
</div>

<script>
const apiBase = ""; // mesma origem

function setActive(btnId) {
  ["btnPastas","btnArquivos","btnBusca","btnStatus"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("active", id === btnId);
  });
}

function showView(view) {
  document.getElementById('viewPastas').style.display   = (view === 'pastas')  ? '' : 'none';
  document.getElementById('viewArquivos').style.display = (view === 'arquivos')? '' : 'none';
  document.getElementById('viewBusca').style.display    = (view === 'busca')   ? '' : 'none';
  document.getElementById('viewStatus').style.display   = (view === 'status')  ? '' : 'none';
  if (view === 'pastas')  { setActive('btnPastas');   loadPastas(); }
  if (view === 'arquivos'){ setActive('btnArquivos'); autoLoadFiles(); }
  if (view === 'busca')   { setActive('btnBusca'); }
  if (view === 'status')  { setActive('btnStatus'); }
}

// Utilidades
const fmtBytes = (b) => {
  if (b == null) return "-";
  const units = ["B","KB","MB","GB","TB"]; let i=0; let val=b;
  while (val >= 1024 && i < units.length-1) { val/=1024; i++; }
  return `${val.toFixed(1)} ${units[i]}`;
};
const fmtDateIso   = (iso)   => iso   ? new Date(iso).toLocaleString() : "-";
const fmtDateEpoch = (epoch) => epoch ? new Date(epoch*1000).toLocaleString() : "-";

// Converte caminho Windows/UNC para file://
function toFileUri(p) {
  const s = String(p || "").replace(/\\/g, "/").replace(/^\/+/, ""); // \\server\share -> server/share
  return "file://///" + s;
}

/* -------- PASTAS (GET /roots) com botões de ação -------- */
async function loadPastas() {
  const msgEl  = document.getElementById('pastasMsg');
  const bodyEl = document.getElementById('pastasBody');
  msgEl.textContent = "Carregando...";
  bodyEl.innerHTML = "";

  try {
    const res = await fetch(`${apiBase}/roots`);
    if (!res.ok) {
      msgEl.textContent = `Erro HTTP ${res.status}: ${res.statusText}`;
      return;
    }
    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      msgEl.textContent = "Nenhuma pasta cadastrada.";
      return;
    }
    msgEl.textContent = "";
    rows.forEach(rf => {
      const tr = document.createElement('tr');

      const tdId = document.createElement('td');            tdId.textContent = rf.id;
      const tdPath = document.createElement('td');          const codePath = document.createElement('code'); codePath.textContent = rf.path || ""; tdPath.appendChild(codePath);
      const tdCount = document.createElement('td');         tdCount.textContent = (rf.files_count ?? '-');
      const tdSize = document.createElement('td');          tdSize.textContent = fmtBytes(rf.total_size_bytes);
      const tdScan = document.createElement('td');          tdScan.textContent = fmtDateIso(rf.last_scan_at);

      const tdActions = document.createElement('td');       tdActions.className = "center";
      const actDiv = document.createElement('div');         actDiv.className = "actions";
      const btnScan = document.createElement('button');     btnScan.className = "btn-sm btn-scan";   btnScan.title = "Executar scan (ler arquivos)"; btnScan.textContent = "Scan";
      const btnIndex = document.createElement('button');    btnIndex.className = "btn-sm btn-index"; btnIndex.title = "Executar indexação";          btnIndex.textContent = "Indexar";

      actDiv.appendChild(btnScan);
      actDiv.appendChild(btnIndex);
      tdActions.appendChild(actDiv);

      tr.appendChild(tdId);
      tr.appendChild(tdPath);
      tr.appendChild(tdCount);
      tr.appendChild(tdSize);
      tr.appendChild(tdScan);
      tr.appendChild(tdActions);

      bodyEl.appendChild(tr);

      btnScan.addEventListener('click', () => runScan(rf.id));
      btnIndex.addEventListener('click', () => runIndex(rf.id));
    });
  } catch (e) {
    msgEl.textContent = `Erro: ${e}`;
  }
}

async function runScan(rootId) {
  const msgEl = document.getElementById('pastasMsg');
  const exts  = document.getElementById('pastasExt').value.trim();

  msgEl.textContent = "Executando scan...";
  try {
    const url = `${apiBase}/scan/${rootId}` + (exts ? `?ext=${encodeURIComponent(exts)}` : "");
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) { msgEl.textContent = `Erro no scan: ${data.detail || res.statusText}`; return; }
    msgEl.textContent = `Scan ok: arquivos=${data.files_count}, tamanho=${fmtBytes(data.total_size_bytes)} (em ${data.elapsed_sec}s)`;
    await loadPastas();
  } catch (e) {
    msgEl.textContent = `Erro no scan: ${e}`;
  }
}

async function runIndex(rootId) {
  const msgEl = document.getElementById('pastasMsg');
  const exts  = document.getElementById('pastasExt').value.trim();

  msgEl.textContent = "Indexando...";
  try {
    const params = new URLSearchParams({ root_id: String(rootId) });
    if (exts) params.append('ext', exts);
    const url = `${apiBase}/index/run?${params.toString()}`;
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) { msgEl.textContent = `Erro na indexação: ${data.detail || res.statusText}`; return; }
    msgEl.textContent = `Indexação: candidatos=${data.candidates}, indexados=${data.indexed}, pulados=${data.skipped}, erros=${data.errors} (em ${data.elapsed_sec}s)`;
  } catch (e) {
    msgEl.textContent = `Erro na indexação: ${e}`;
  }
}

/* -------- ARQUIVOS (GET /files) em tabela + botões -------- */
async function loadFiles() {
  const rootId = document.getElementById('filesRootId').value.trim();
  const ext    = document.getElementById('filesExt').value.trim();
  const limit  = document.getElementById('filesLimit').value.trim() || "100";
  const msg    = document.getElementById('filesMsg');
  const body   = document.getElementById('filesBody');

  msg.textContent = "Carregando...";
  body.innerHTML = "";
  const trLoading = document.createElement('tr');
  const tdLoading = document.createElement('td');
  tdLoading.colSpan = 6; tdLoading.className = "muted"; tdLoading.textContent = "Carregando...";
  trLoading.appendChild(tdLoading); body.appendChild(trLoading);

  try {
    const params = new URLSearchParams({ limit: String(limit) });
    if (rootId) params.append('root_id', rootId);
    if (ext)    params.append('ext', ext);

    const res = await fetch(`${apiBase}/files?${params.toString()}`);
    if (!res.ok) {
      const txt = await res.text();
      msg.textContent = `Erro HTTP ${res.status}: ${txt || res.statusText}`;
      body.innerHTML = "";
      const trFail = document.createElement('tr'); const tdFail = document.createElement('td');
      tdFail.colSpan = 6; tdFail.className = "muted"; tdFail.textContent = "Falha ao carregar.";
      trFail.appendChild(tdFail); body.appendChild(trFail);
      return;
    }

    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      msg.textContent = "Nenhum arquivo encontrado.";
      body.innerHTML = "";
      const trEmpty = document.createElement('tr'); const tdEmpty = document.createElement('td');
      tdEmpty.colSpan = 6; tdEmpty.className = "muted"; tdEmpty.textContent = "Nenhum arquivo encontrado.";
      trEmpty.appendChild(tdEmpty); body.appendChild(trEmpty);
      return;
    }

    msg.textContent = `Encontrados: ${rows.length}`;
    body.innerHTML = "";

    rows.forEach(r => {
      const tr = document.createElement('tr');

      const tdName = document.createElement('td'); tdName.textContent = r.name || "";
      const tdExt  = document.createElement('td'); tdExt.className = "nowrap"; tdExt.textContent = r.ext || "";
      const tdSize = document.createElement('td'); tdSize.className = "nowrap"; tdSize.textContent = fmtBytes(r.size);
      const tdMt   = document.createElement('td'); tdMt.className   = "nowrap"; tdMt.textContent = fmtDateEpoch(r.mtime);

      const tdPath = document.createElement('td'); const codePath = document.createElement('code'); codePath.textContent = r.path || ""; tdPath.appendChild(codePath);

      const tdActions = document.createElement('td'); tdActions.className = "center"; const divAct = document.createElement('div'); divAct.className = "actions";
      const btnOpen = document.createElement('button'); btnOpen.className = "btn-sm btn-open"; btnOpen.title = "Abrir via file://"; btnOpen.textContent = "Abrir";
      const btnDown = document.createElement('button'); btnDown.className = "btn-sm btn-download"; btnDown.title = "Download via HTTP"; btnDown.textContent = "Download";
      const btnCopy = document.createElement('button'); btnCopy.className = "btn-sm btn-copy"; btnCopy.title = "Copiar caminho"; btnCopy.textContent = "Copiar";

      divAct.appendChild(btnOpen); divAct.appendChild(btnDown); divAct.appendChild(btnCopy); tdActions.appendChild(divAct);

      tr.appendChild(tdName); tr.appendChild(tdExt); tr.appendChild(tdSize); tr.appendChild(tdMt); tr.appendChild(tdPath); tr.appendChild(tdActions);
      body.appendChild(tr);

      const fileUri     = toFileUri(r.path);
      const downloadUrl = "/download?path=" + encodeURIComponent(r.path || "");

      btnOpen.addEventListener('click', () => { window.open(fileUri, '_blank', 'noopener'); });
      btnDown.addEventListener('click', () => { window.open(downloadUrl, '_blank', 'noopener'); });
      btnCopy.addEventListener('click', async () => {
        try { await navigator.clipboard.writeText(r.path || ""); msg.textContent = "Caminho copiado."; }
        catch (e) { msg.textContent = "Falha ao copiar. Copie manualmente o texto do campo Caminho."; }
      });
    });
  } catch (e) {
    msg.textContent = `Erro: ${e}`;
    body.innerHTML = "";
    const trErr = document.createElement('tr'); const tdErr = document.createElement('td');
    tdErr.colSpan = 6; tdErr.className = "muted"; tdErr.textContent = "Erro ao listar arquivos.";
    trErr.appendChild(tdErr); body.appendChild(trErr);
  }
}

function autoLoadFiles() {
  const rootId = document.getElementById('filesRootId').value.trim();
  if (rootId) loadFiles();
}

/* -------- BUSCA (GET /search) em TABELA + botões -------- */
async function runSearch() {
  const rootId = document.getElementById('searchRootId').value.trim();
  const q      = document.getElementById('searchQuery').value.trim();
  const ext    = document.getElementById('searchExt').value.trim();
  const limit  = document.getElementById('searchLimit').value.trim() || "50";
  const msg    = document.getElementById('searchMsg');
  const body   = document.getElementById('searchBody');

  if (!q) { msg.textContent = "Informe a consulta."; return; }
  msg.textContent = "Buscando...";
  body.innerHTML = "";
  const trLoading = document.createElement('tr');
  const tdLoading = document.createElement('td');
  tdLoading.colSpan = 5; tdLoading.className = "muted"; tdLoading.textContent = "Buscando...";
  trLoading.appendChild(tdLoading); body.appendChild(trLoading);

  try {
    const params = new URLSearchParams({ q, limit: String(limit) });
    if (rootId) params.append('root_id', rootId);
    if (ext)    params.append('ext', ext);

    const res = await fetch(`${apiBase}/search?${params.toString()}`);
    if (!res.ok) {
      const txt = await res.text();
      msg.textContent = `Erro HTTP ${res.status}: ${txt || res.statusText}`;
      body.innerHTML = "";
      const trFail = document.createElement('tr'); const tdFail = document.createElement('td');
      tdFail.colSpan = 5; tdFail.className = "muted"; tdFail.textContent = "Falha na busca.";
      trFail.appendChild(tdFail); body.appendChild(trFail);
      return;
    }

    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      msg.textContent = "Nenhum resultado.";
      body.innerHTML = "";
      const trEmpty = document.createElement('tr'); const tdEmpty = document.createElement('td');
      tdEmpty.colSpan = 5; tdEmpty.className = "muted"; tdEmpty.textContent = "Nenhum resultado.";
      trEmpty.appendChild(tdEmpty); body.appendChild(trEmpty);
      return;
    }

    msg.textContent = `Resultados: ${rows.length}`;
    body.innerHTML = "";

    rows.forEach(r => {
      const tr = document.createElement('tr');

      const tdName = document.createElement('td'); tdName.textContent = r.name || "";
      const tdExt  = document.createElement('td'); tdExt.className = "nowrap"; tdExt.textContent = r.ext || "";

      const tdPath = document.createElement('td');
      const codePath = document.createElement('code'); codePath.textContent = r.path || "";
      tdPath.appendChild(codePath);

      const tdSnip = document.createElement('td');
      tdSnip.textContent = r.snippet || "";

      const tdActions = document.createElement('td'); tdActions.className = "center"; const divAct = document.createElement('div'); divAct.className = "actions";
      const btnOpen = document.createElement('button'); btnOpen.className = "btn-sm btn-open"; btnOpen.title = "Abrir via file://"; btnOpen.textContent = "Abrir";
      const btnDown = document.createElement('button'); btnDown.className = "btn-sm btn-download"; btnDown.title = "Download via HTTP"; btnDown.textContent = "Download";
      const btnCopy = document.createElement('button'); btnCopy.className = "btn-sm btn-copy"; btnCopy.title = "Copiar caminho"; btnCopy.textContent = "Copiar";

      divAct.appendChild(btnOpen); divAct.appendChild(btnDown); divAct.appendChild(btnCopy); tdActions.appendChild(divAct);

      tr.appendChild(tdName); tr.appendChild(tdExt); tr.appendChild(tdPath); tr.appendChild(tdSnip); tr.appendChild(tdActions);
      body.appendChild(tr);

      const fileUri     = toFileUri(r.path);
      const downloadUrl = r.download_url || ("/download?path=" + encodeURIComponent(r.path || ""));

      btnOpen.addEventListener('click', () => { window.open(fileUri, '_blank', 'noopener'); });
      btnDown.addEventListener('click', () => { window.open(downloadUrl, '_blank', 'noopener'); });
      btnCopy.addEventListener('click', async () => {
        try { await navigator.clipboard.writeText(r.path || ""); msg.textContent = "Caminho copiado."; }
        catch (e) { msg.textContent = "Falha ao copiar. Copie manualmente o texto do campo Caminho."; }
      });
    });
  } catch (e) {
    msg.textContent = `Erro: ${e}`;
    body.innerHTML = "";
    const trErr = document.createElement('tr'); const tdErr = document.createElement('td');
    tdErr.colSpan = 5; tdErr.className = "muted"; tdErr.textContent = "Erro ao processar resultados.";
    trErr.appendChild(tdErr); body.appendChild(trErr);
  }
}

/* -------- STATUS -------- */
async function checkHealth() {
  const msg = document.getElementById('healthMsg');
  msg.textContent = "Checando...";
  try {
    const res = await fetch(`${apiBase}/health`);
    const data = await res.json();
    msg.textContent = `Status: ${JSON.stringify(data)}`;
  } catch (e) {
    msg.textContent = `Erro ao consultar health: ${e}`;
  }
}

/* -------- Eventos -------- */
document.getElementById('btnPastas').addEventListener('click', () => showView('pastas'));
document.getElementById('btnArquivos').addEventListener('click', () => showView('arquivos'));
document.getElementById('btnBusca').addEventListener('click', () => showView('busca'));
document.getElementById('btnStatus').addEventListener('click', () => showView('status'));

document.getElementById('btnFilesLoad').addEventListener('click', () => loadFiles());
document.getElementById('btnSearchRun').addEventListener('click', () => runSearch());
document.getElementById('btnHealthCheck').addEventListener('click', () => checkHealth());
document.getElementById('btnReloadRoots').addEventListener('click', () => loadPastas());

// Inicial: mostra 'Pastas' e carrega GET /roots automaticamente
showView('pastas');
</script>
</body>
</html>
    """
    return HTMLResponse(content=html, status_code=200)
