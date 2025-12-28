
# -*- coding: utf-8 -*-
"""
app_arquivos.py
- Página de listagem de metadados dos arquivos em formato de TABELA.
- Filtros: root_id, ext, limit.
- Links: file:// (direto) e /download (HTTP).
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/app", tags=["App UI"])

@router.get("/arquivos", response_class=HTMLResponse)
def render_arquivos_page():
    html = r"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Arquivos (Metadados)</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root { --bg:#0f172a; --panel:#111827; --border:#1f2937; --text:#e5e7eb; --muted:#94a3b8; }
    * { box-sizing: border-box; }
    body { margin:0; background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Arial; }
    header { padding: 12px 16px; background:#0b1220; border-bottom:1px solid var(--border); }
    header h1 { margin:0; font-size:18px; }
    main { padding: 12px 16px; }
    .panel { background: var(--panel); border:1px solid var(--border); border-radius:10px; padding:12px; margin-bottom:12px; }
    label { display:block; font-size:13px; color:var(--muted); margin-bottom:6px; }
    input[type=text] { width:100%; padding:10px 12px; border-radius:8px; border:1px solid var(--border); background:#0b1220; color:var(--text); }
    .row { display:flex; gap:12px; align-items:flex-end; flex-wrap:wrap; }
    .row > div { flex:1; min-width:220px; }
    .btn { padding:8px 12px; border-radius:8px; border:1px solid var(--border); color:#fff; background:#1f2937; cursor:pointer; font-size:13px; }
    .btn:hover { filter: brightness(1.08); }
    .btn-info { background:#1855b3; border-color:#144896; }
    .muted { color: var(--muted); }
    table { width:100%; border-collapse: collapse; margin-top:8px; }
    th, td { border-bottom:1px solid var(--border); padding:8px; font-size:13px; vertical-align: top; }
    th { text-align:left; color: var(--muted); }
    code { background:#0b1220; padding:2px 6px; border-radius:6px; border:1px solid var(--border); word-break: break-all; }
    .nowrap { white-space: nowrap; }
    .center { text-align: center; }
    .msg { margin-top:8px; font-size:13px; }
    .small { font-size:12px; }
    .links a { color:#93c5fd; text-decoration:none; margin-right:8px; }
    .links a:hover { text-decoration:underline; }
  </style>
</head>
<body>
<header><h1>Arquivos (Metadados)</h1></header>
<main>
  <!-- Filtros -->
  <div class="panel">
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
        <button class="btn btn-info" onclick="loadFiles()">Carregar</button>
      </div>
    </div>
    <div class="msg muted" id="filesMsg"></div>
  </div>

  <!-- Tabela -->
  <div class="panel">
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
</main>

<script>
const apiBase = ""; // mesma origem

const fmtBytes = (b) => {
  if (b == null) return "-";
  const units = ["B","KB","MB","GB","TB"]; let i=0; let val=b;
  while (val >= 1024 && i < units.length-1) { val/=1024; i++; }
  return `${val.toFixed(1)} ${units[i]}`;
};
const fmtDate = (epoch) => epoch ? new Date(epoch*1000).toLocaleString() : "-";

// Converte caminho Windows/UNC para file:// URI
function toFileUri(p) {
  // \\server\share\dir\file.ext -> file://///server/share/dir/file.ext
  const s = String(p || "").replace(/\\/g, "/").replace(/^\/+/, "");
  return "file://///" + s;
}

async function loadFiles() {
  const rootId = document.getElementById('filesRootId').value.trim();
  const ext    = document.getElementById('filesExt').value.trim();
  const limit  = document.getElementById('filesLimit').value.trim() || "100";
  const msg    = document.getElementById('filesMsg');
  const body   = document.getElementById('filesBody');

  msg.textContent = "Carregando...";
  body.innerHTML = `<tr><td colspan="6" class="muted">Carregando...</td></tr>`;

  try {
    const params = new URLSearchParams({ limit: String(limit) });
    if (rootId) params.append('root_id', rootId);
    if (ext)    params.append('ext', ext);

    const res = await fetch(`${apiBase}/files?${params.toString()}`);
    if (!res.ok) {
      const txt = await res.text();
      msg.textContent = `Erro HTTP ${res.status}: ${txt || res.statusText}`;
      body.innerHTML = `<tr><td colspan="6" class="muted">Falha ao carregar.</td></tr>`;
      return;
    }

    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length === 0) {
      msg.textContent = "Nenhum arquivo encontrado.";
      body.innerHTML = `<tr><td colspan="6" class="muted">Nenhum arquivo encontrado.</td></tr>`;
      return;
    }

    msg.textContent = `Encontrados: ${rows.length}`;
    const html = rows.map(r => {
      const fileUri = toFileUri(r.path);
      const downloadUrl = `/download?path=${encodeURIComponent(r.path)}`;
      return `
        <tr>
          <td>${r.name}</td>
          <td class="nowrap">${r.ext || ""}</td>
          <td class="nowrap">${fmtBytes(r.size)}</td>
          <td class="nowrap">${fmtDate(r.mtime)}</td>
          <td><code>${r.path}</code></td>
          <td class="center">
            <div class="links">
              ${fileUri}file://</a>
              ${downloadUrl}download</a>
            </div>
          </td>
        </tr>
      `;
    }).join("");

    body.innerHTML = html;
  } catch (e) {
    msg.textContent = `Erro: ${e}`;
    body.innerHTML = `<tr><td colspan="6" class="muted">Erro ao listar arquivos.</td></tr>`;
  }
}
</script>
</body>
</html>
    """
    return HTMLResponse(content=html, status_code=200)
