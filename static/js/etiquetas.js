const hoje = new Date().toLocaleDateString("pt-BR");

function atualizarLinksPDF(codigo) {
  const links = [
    document.getElementById("pdfPreviewLink"),
    document.getElementById("pdfPreviewLinkAside")
  ];

  links.forEach((link) => {
    if (!link) return;

    if (codigo && codigo !== "MP-0000") {
      link.href = `/etiquetas/pdf/${encodeURIComponent(codigo)}`;
      link.classList.remove("disabled-link");
    } else {
      link.href = "#";
      link.classList.add("disabled-link");
    }
  });
}

function preencherMaterial() {
  const select = document.getElementById("codigo");
  const selected = select.options[select.selectedIndex];

  if (!selected) return;

  document.getElementById("descricao").value = selected.dataset.descricao || "";
  document.getElementById("lote").value = selected.dataset.lote || "";
  document.getElementById("quantidade").value = selected.dataset.qtd || "";
  document.getElementById("localizacao").value = selected.dataset.local || "";

  const status = selected.dataset.status || "Ativa";
  const statusSelect = document.getElementById("statusEtiqueta");
  if (statusSelect && ["Ativa", "Gerada", "Pendente", "Reimpressão"].includes(status)) {
    statusSelect.value = status;
  }

  atualizarPreview();
}

function atualizarPreview() {
  const codigo = document.getElementById("codigo").value || "MP-0000";
  const lote = document.getElementById("lote").value || "-";
  const descricao = document.getElementById("descricao").value || "Descrição do material";
  const quantidade = document.getElementById("quantidade").value || "-";
  const localizacao = document.getElementById("localizacao").value || "-";
  const status = document.getElementById("statusEtiqueta").value || "Ativa";

  document.getElementById("previewCodigo").textContent = codigo;
  document.getElementById("previewLote").textContent = lote;
  document.getElementById("previewDescricao").textContent = descricao;
  document.getElementById("previewQuantidade").textContent = quantidade;
  document.getElementById("previewLocal").textContent = localizacao;
  document.getElementById("previewStatus").textContent = status;

  const dataEl = document.getElementById("previewData");
  if (dataEl) dataEl.textContent = hoje;

  const qr = document.getElementById("qr");

  if (codigo && codigo !== "MP-0000" && qr) {
    qr.innerHTML = `<img src="/qrcode/material/${encodeURIComponent(codigo)}" width="120" alt="QR Code ${codigo}">`;
  } else if (qr) {
    qr.innerHTML = `<span class="qr-placeholder">QR</span>`;
  }

  atualizarLinksPDF(codigo);
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

function carregarEtiquetaNaPrevia(dados) {
  document.getElementById("previewCodigo").textContent = dados.codigo || "-";
  document.getElementById("previewDescricao").textContent = dados.descricao || "-";
  document.getElementById("previewLote").textContent = dados.lote || "-";
  document.getElementById("previewQuantidade").textContent = dados.quantidade || "-";
  document.getElementById("previewLocal").textContent = dados.localizacao || "-";
  document.getElementById("previewStatus").textContent = dados.status || "Gerada";

  const dataEl = document.getElementById("previewData");
  if (dataEl) dataEl.textContent = hoje;

  const qr = document.getElementById("qr");
  if (qr && dados.codigo) {
    qr.innerHTML = `<img src="/qrcode/material/${encodeURIComponent(dados.codigo)}" alt="QR Code ${dados.codigo}">`;
  }

  atualizarLinksPDF(dados.codigo || "");
}

function imprimirEtiquetaTabela(codigo, descricao, lote, quantidade, localizacao, status) {
  carregarEtiquetaNaPrevia({ codigo, descricao, lote, quantidade, localizacao, status });
  prepararImpressao();
}

function limparFormulario() {
  document.getElementById("codigo").value = "";
  document.getElementById("lote").value = "";
  document.getElementById("descricao").value = "";
  document.getElementById("quantidade").value = "";
  document.getElementById("localizacao").value = "";
  document.getElementById("statusEtiqueta").value = "Ativa";

  const success = document.getElementById("successMessage");
  if (success) success.classList.remove("show");

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

document.addEventListener("DOMContentLoaded", () => {
  atualizarPreview();

  document.querySelectorAll(".print-label-btn").forEach((botao) => {
    botao.addEventListener("click", () => {
      carregarEtiquetaNaPrevia({
        codigo: botao.dataset.codigo,
        descricao: botao.dataset.descricao,
        lote: botao.dataset.lote,
        quantidade: botao.dataset.quantidade,
        localizacao: botao.dataset.localizacao,
        status: botao.dataset.status
      });
      prepararImpressao();
    });
  });

  document.querySelectorAll(".disabled-link").forEach((link) => {
    link.addEventListener("click", (event) => {
      if (link.classList.contains("disabled-link")) {
        event.preventDefault();
      }
    });
  });
});
