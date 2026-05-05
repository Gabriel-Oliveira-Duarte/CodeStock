const hoje = new Date().toISOString().split("T")[0];

function preencherMaterial() {
  const select = document.getElementById("codigo");
  const selected = select.options[select.selectedIndex];

  if (!selected) return;

  document.getElementById("descricao").value = selected.dataset.descricao || "";
  document.getElementById("lote").value = selected.dataset.lote || "";
  document.getElementById("quantidade").value = selected.dataset.qtd || "";
  document.getElementById("localizacao").value = selected.dataset.local || "";

  atualizarPreview();
}

function atualizarPreview() {
  const codigo = document.getElementById("codigo").value || "MP-0000";
  const lote = document.getElementById("lote").value || "—";
  const descricao = document.getElementById("descricao").value || "Descrição do material";
  const quantidade = document.getElementById("quantidade").value || "—";
  const localizacao = document.getElementById("localizacao").value || "—";
  const status = document.getElementById("statusEtiqueta").value || "Ativa";

  document.getElementById("previewCodigo").textContent = codigo;
  document.getElementById("previewLote").textContent = lote;
  document.getElementById("previewDescricao").textContent = descricao;
  document.getElementById("previewQuantidade").textContent = quantidade;
  document.getElementById("previewLocal").textContent = localizacao;
  document.getElementById("previewStatus").textContent = status;

  const qr = document.getElementById("qr");

  if (codigo && qr) {
    qr.innerHTML = `<img src="/qrcode/material/${codigo}" width="120" alt="QR Code ${codigo}">`;
  }
}

function gerarQR() {
  atualizarPreview();

  const success = document.getElementById("successMessage");
  if (success) {
    success.classList.add("show");
  }
}

function prepararImpressao() {
  document.body.classList.add("modo-impressao-etiqueta");

  setTimeout(() => {
    window.print();
  }, 200);

  setTimeout(() => {
    document.body.classList.remove("modo-impressao-etiqueta");
  }, 1000);
}

function imprimirEtiqueta() {
  atualizarPreview();
  prepararImpressao();
}

function imprimirEtiquetaTabela(codigo, descricao, lote, quantidade, localizacao, status) {
  document.getElementById("previewCodigo").textContent = codigo || "—";
  document.getElementById("previewDescricao").textContent = descricao || "—";
  document.getElementById("previewLote").textContent = lote || "—";
  document.getElementById("previewQuantidade").textContent = quantidade || "—";
  document.getElementById("previewLocal").textContent = localizacao || "—";
  document.getElementById("previewStatus").textContent = status || "Gerada";

  const qr = document.getElementById("qr");

  if (qr && codigo) {
    qr.innerHTML = `<img src="/qrcode/material/${codigo}" alt="QR Code ${codigo}">`;
  }

  prepararImpressao();
}

function limparFormulario() {
  document.getElementById("codigo").value = "";
  document.getElementById("lote").value = "";
  document.getElementById("descricao").value = "";
  document.getElementById("quantidade").value = "";
  document.getElementById("localizacao").value = "";
  document.getElementById("statusEtiqueta").value = "Ativa";

  document.getElementById("qr").innerHTML = "";

  document.getElementById("successMessage").classList.remove("show");

  atualizarPreview();
}

function filtrarTabela() {
  const busca = document.getElementById("busca").value.toLowerCase();
  const status = document.getElementById("statusFiltro").value.toLowerCase();
  const linhas = document.querySelectorAll("#etiquetasTabela tbody tr");

  linhas.forEach((linha) => {
    const texto = linha.innerText.toLowerCase();
    const combinaBusca = texto.includes(busca);
    const combinaStatus = status === "" || texto.includes(status);

    linha.style.display = combinaBusca && combinaStatus ? "" : "none";
  });
}

function limparFiltros() {
  document.getElementById("busca").value = "";
  document.getElementById("statusFiltro").value = "";
  filtrarTabela();
}