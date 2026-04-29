const hoje = new Date().toISOString().split("T")[0];

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
}

function gerarQR() {
  atualizarPreview();

  const qr = document.getElementById("qr");
  const success = document.getElementById("successMessage");

  qr.style.animation = "none";
  setTimeout(() => {
    qr.style.animation = "pulse 0.45s ease";
  }, 10);

  success.classList.add("show");
}

function imprimirEtiqueta() {
  window.print();
}

function limparFormulario() {
  document.getElementById("codigo").value = "";
  document.getElementById("lote").value = "";
  document.getElementById("descricao").value = "";
  document.getElementById("quantidade").value = "";
  document.getElementById("localizacao").value = "";
  document.getElementById("statusEtiqueta").value = "Ativa";
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
