# -*- coding: utf-8 -*-
"""
app_pastas.py
- Página completa para cadastro/gestão de pastas raiz.
- Exibe grid com ações: Scan, Indexar, Arquivos, Buscar, Editar, Excluir.
- Integra diretamente com os endpoints:
  /roots (CRUD), /scan/{id}, /index/run, /files, /search, /download
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/app", tags=["App UI"])

@router.get("/pastas", response_class=HTMLResponse)
def render_pastas_page():
    html = r"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Pastas Raiz</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { --bg:#0f172a; --panel:#111827; --border:#1f2937; --text:#e5e7eb; --muted:#94a3b8; --ok:#22c55e; --warn:#f59e0b; --err:#ef4444; --info:#3b82f6; }
    * { box-sizing: border-box; }
    body { margin:0; background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial; }
    header { padding: 12px 16px; background:#0b1220; border-bottom:1px solid var(--border); }
    header h1 { margin:0; font-size:18px; }
    main { padding: 12px 16px; }
    .panel { background: var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px; margin-bottom:12px; }
    label { display:block; font-size:13px; color:var(--muted); margin-bottom:6px; }
    input[type=text] { width:100%; padding:10px 12px; border-radius:8px; border:1px solid var(--border); background:#0b1220; color:var(--text); }
    .row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
    .row > * { flex:1; min-width: 220px; }
    .btn { padding:8px 12px; border-radius:8px; border:1px solid var(--border); color:#fff; background:#1f2937; cursor:pointer; font-size:13px; }
    .btn:hover { filter: brightness(1.06); }
    .btn-primary { background:#0b5; border-color:#0a4; }
    .btn-warn { background:#b7810a; border-color:#a97008; }
    .btn-danger { background:#b0152b; border-color:#8b1123; }
    .btn-info { background:#1855b3; border-color:#144896; }
    table { width:100%; border-collapse: collapse; margin-top:8px; }
    th, td { border-bottom:1px solid var(--border); padding:8px; font-size:13px; vertical-align: top; }
    th { text-align:left; color:var(--muted); }
    code { background:#0b1220; padding:2px 6px; border-radius:6px; border:1px solid var(--border); }
    .muted { color: var(--muted); }
    .pill { display:inline-block; padding: 2px 8px; border-radius:999px; font-size:12px; border:1px solid var(--border); background:#0b1220; }
    .grid-actions { display:flex; gap:6px; flex-wrap:wrap; }
    .msg { margin-top:8px; font-size:13px; }
    .msg.ok { color: var(--ok); }
    .msg.warn { color: var(--warn); }
    .msg.err { color: var(--err); }
    .results { background:#0b1220; border:1px solid var(--border); border-radius:10px; padding:12px; margin-top:10px; }
    .result-item { border-bottom:1px solid var(--border); padding:8px 0; }
    .result-item:last-child { border-bottom:0; }
    .link { color:#93c5fd; text-decoration:none; }
    .link:hover { text-decoration:underline; }
    .small { font-size:12px; }
  </style>
</head>
<body>
<header><h1>Pastas Raiz</h1></header>
<main>
  <!-- Cadastro -->
  <div class="panel">
    <div class="row">
      <div>
        <label for="rootPath">Caminho (UNC ou local)</label>
        <input id="rootPath" type="text" placeholder="Ex.: \\filesrv\eng\projetos">
      </div>
      <div style="flex:0 0 auto;">
        <button class="btn btn-primary" onclick="createRoot()">Adicionar</button>
      </div>
    </div>
    <div class="msg" id="createMsg"></div>
  </div>

  <!-- Filtros/acoes globais -->
  <div class="panel">
    <div class="row" style="align-items:flex-end;">
      <div>
        <label for="extFilter">Extensões (scan/index)</label>
        <input id="extFilter" type="text" value="pdf,docx,pptx,xlsx,txt,csv" />
      </div>
      <div>
        <label for="searchQuery">Busca (full-text)</label>
        <input id="searchQuery" type="text" placeholder='Ex.: "válvula de retenção" AND inox' />
      </div>
      <div>
        <label for="searchExt">Extensões (busca)</label>
        <input id="searchExt" type="text" value="pdf,docx,txt" />
      </div>
      <div>
        <label for="searchLimit">Limite</label>
        <input id="searchLimit" type="text" value="50" />
      </div>
    </div>
  </div>

  <!-- Grid de pastas -->
  <div class="panel">
    <table>
      <thead>
        <tr>
          <th>ID</th>
          <th>Path</th>
          <th class="muted">files_count</th>
          <th class="muted">total_size</th>
          <th class="muted">last_scan_at</th>
          <th>Ações</th>
        </tr>
      </thead>
      <tbody id="rootsBody">
        <tr><td colspan="6" class="muted">Carregando...</td></tr>
      </tbody>
    </table>
    <div class="msg" id="gridMsg"></div>
  </div>

  <!-- Resultados -->
  <div class="panel">
    <div class="results" id="results"></div>
  </div>
</main>

<script>
const apiBase = ""; // mesma origem
const fmtBytes = (b) => {
  if (b == null) return "-";
  const units = ["B","KB","MB","GB","TB"]; let i=0; let val=b;
  while (val >= 1024 && i < units.length-1) { val/=1024; i++;
  }
  return `${val.toFixed(1)} ${units[i]}`;
};
const fmtDate = (iso) => iso ? new Date(iso).toLocaleString() : "-";

function setMsg(id, text, cls="") {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `msg ${cls}`;
  el.textContent = text;
}

async function createRoot() {
  const path = document.getElementById('rootPath').value.trim();
  if (!path) { setMsg('createMsg', "Informe o caminho.", "warn"); return; }
  setMsg('createMsg', "");

  try {
    const res = await fetch(`${apiBase}/roots`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ path })
    });
    if (!res.ok) {
      const err = await res.json().catch(()=>({detail: res.statusText}));
      setMsg('createMsg', `Erro: ${err.detail || res.statusText}`, "err");
      return;
    }
    document.getElementById('rootPath').value = "";
    setMsg('createMsg', "Pasta adicionada com sucesso.", "ok");
    await loadRoots();
  } catch (e) {
    setMsg('createMsg', `Falha: ${e}`, "err");
  }
}

async function loadRoots() {
  const body = document.getElementById('rootsBody');
  body.innerHTML = `<tr><td colspan="6" class="muted">Carregando...</td></tr>`;
  setMsg('gridMsg', "");
  try {
    const res = await fetch(`${apiBase}/roots`);
    if (!res.ok) {
      body.innerHTML = `<tr><td colspan="6" class="muted">Erro HTTP ${res.status}: ${res.statusText}</td></tr>`;
      return;
    }
    const rows = await res.json();
    if (!Array.isArray(rows)) {
      body.innerHTML = `<tr><td colspan="6" class="muted">Resposta inesperada.</td></tr>`;
      return;
    }
    if (rows.length === 0) {
      body.innerHTML = `<tr><td colspan="6" class="muted">Nenhuma pasta cadastrada.</td></tr>`;
      return;
    }
    body.innerHTML = "";
    for (const rf of rows) {
      const tr = document.createElement('tr');
      const safePath = String(rf.path || "").replace(/\\/g, '\\\\'); // para usar em onclick
      tr.innerHTML = `
        <td>${rf.id}</td>
        <td><code>${rf.path}</code></td>
        <td class="small">${rf.files_count ?? '-'}</td>
        <td class="small">${fmtBytes(rf.total_size_bytes)}</td>
        <td class="small">${fmtDate(rf.last_scan_at)}</td>
        <td>
          <div class="grid-actions">
            <button class="btn btn-warn" onclick="runScan(${rf.id})">Scan</button>
            <button class="btn btn-primary" onclick="runIndex(${rf.id})">Indexar</button>
            <button class="btn btn-info" onclick="listFiles(${rf.id})">Arquivos</button>
            <button class="btn" onclick="searchRoot(${rf.id})">Buscar</button>
            <button class="btn" onclick="editRoot(${rf.id}, '${safePath}')">Editar</button>
            <button class="btn btn-danger" onclick="deleteRoot(${rf.id})">Excluir</button>
          </div>
        </td>
      `;
      body.appendChild(tr);
    }
  } catch (e) {
    body.innerHTML = `<tr><td colspan="6" class="muted">Erro ao carregar: ${e}</td></tr>`;
  }
}

async function runScan(id) {
  const exts = document.getElementById('extFilter').value.trim();
  setMsg('gridMsg', "Executando scan...", "info");
  try {
    const url = `${apiBase}/scan/${id}` + (exts ? `?ext=${encodeURIComponent(exts)}` : "");
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      setMsg('gridMsg', `Erro no scan: ${data.detail || res.statusText}`, "err");
      return;
    }
    setMsg('gridMsg', `Scan ok: arquivos=${data.files_count}, tamanho=${fmtBytes(data.total_size_bytes)} (em ${data.elapsed_sec}s)`, "ok");
    await loadRoots();
  } catch (e) {
    setMsg('gridMsg', `Erro no scan: ${e}`, "err");
  }
}

async function runIndex(id) {
  const exts = document.getElementById('extFilter').value.trim();
  setMsg('gridMsg', "Indexando...", "info");
  try {
    const params = new URLSearchParams({ root_id: String(id) });
    if (exts) params.append('ext', exts);
    const url = `${apiBase}/index/run?${params.toString()}`;
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      setMsg('gridMsg', `Erro na indexação: ${data.detail || res.statusText}`, "err");
      return;
    }
    setMsg('gridMsg', `Indexação: candidatos=${data.candidates}, indexados=${data.indexed}, pulados=${data.skipped}, erros=${data.errors} (em ${data.elapsed_sec}s)`, "ok");
  } catch (e) {
    setMsg('gridMsg', `Erro na indexação: ${e}`, "err");
  }
}

async function listFiles(id) {
  const results = document.getElementById('results');
  results.innerHTML = `<div class="muted">Carregando arquivos...</div>`;
  try {
    const params = new URLSearchParams({ root_id: String(id), limit: "100" });
    const res = await fetch(`${apiBase}/files?${params.toString()}`);
    if (!res.ok) {
      const txt = await res.text();
      results.innerHTML = `<div class="muted">Erro HTTP ${res.status}: ${txt || res.statusText}</div>`;
      return;
    }
    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      results.innerHTML = `<div class="muted">Nenhum arquivo encontrado nessa raiz.</div>`;
      return;
    }
    const html = rows.map(r => `
      <div class="result-item">
        <div><strong>${r.name}</strong> <span class="pill">${r.ext || ''}</span></div>
        <div class="small muted">${r.path}</div>
        <div class="small">size=${fmtBytes(r.size)} mtime=${r.mtime ? new Date(r.mtime*1000).toLocaleString() : '-'}</div>
        <div class="small"><a class="link" href="/download?path=${encodeURIComponentr</a></div>
      </div>
    `).join("");
    results.innerHTML = html;
  } catch (e) {
    results.innerHTML = `<div class="muted">Erro ao listar arquivos: ${e}</div>`;
  }
}

async function searchRoot(id) {
  const q = document.getElementById('searchQuery').value.trim();
  const ext = document.getElementById('searchExt').value.trim();
  const limit = parseInt(document.getElementById('searchLimit').value.trim() || '50', 10);
  const results = document.getElementById('results');

  if (!q) { results.innerHTML = `<div class="muted">Informe uma consulta em "Busca".</div>`; return; }

  results.innerHTML = `<div class="muted">Buscando...</div>`;
  try {
    const params = new URLSearchParams({ q, limit: String(limit), root_id: String(id) });
    if (ext) params.append('ext', ext);
    const url = `${apiBase}/search?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) {
      const txt = await res.text();
      results.innerHTML = `<div class="muted">Erro HTTP ${res.status}: ${txt || res.statusText}</div>`;
      return;
    }
    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      results.innerHTML = `<div class="muted">Nenhum resultado.</div>`;
      return;
    }
    const html = rows.map(r => `
      <div class="result-item">
        <div><strong>${r.name}</strong> <span class="pill">${r.ext}</span> <span class="pill">score=${(r.score ?? 0).toFixed(2)}</span></div>
        <div class="small muted">${r.path}</div>
        ${r.snippet ? `<div class="small">${r.snippet}</div>` : ''}
        <div class="small">
          ${r.download_url}Abrir / Baixar</a> 
          &nbsp;|&nbsp; 
          ${r.file_uri}file://</a>
        </div>
      </div>
    `).join("");
    results.innerHTML = html;
  } catch (e) {
    results.innerHTML = `<div class="muted">Erro na busca: ${e}</div>`;
  }
}

async function editRoot(id, currentPath) {
  const newPath = prompt("Novo path para a raiz:", currentPath);
  if (newPath === null) return; // cancelado
  setMsg('gridMsg', "");
  try {
    const res = await fetch(`${apiBase}/roots/${id}`, {
      method: 'PUT',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ path: newPath })
    });
    if (!res.ok) {
      const err = await res.json().catch(()=>({detail: res.statusText}));
      setMsg('gridMsg', `Erro ao editar: ${err.detail || res.statusText}`, "err");
      return;
    }
    setMsg('gridMsg', "Path atualizado.", "ok");
    await loadRoots();
  } catch (e) {
    setMsg('gridMsg', `Falha ao editar: ${e}`, "err");
  }
}

async function deleteRoot(id) {
  if (!confirm("Confirma excluir esta raiz?")) return;
  setMsg('gridMsg', "");
  try {
    const res = await fetch(`${apiBase}/roots/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      const txt = await res.text();
      setMsg('gridMsg', `Erro ao excluir: ${txt || res.statusText}`, "err");
      return;
    }
    setMsg('gridMsg', "Raiz excluída.", "ok");
    await loadRoots();
  } catch (e) {
    setMsg('gridMsg', `Falha ao excluir: ${e}`, "err");
  }
}

// Inicializa
loadRoots();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html, status_code=200)
