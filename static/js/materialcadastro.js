document.addEventListener("DOMContentLoaded", function () {
  const dataEntrada = document.getElementById("dataEntrada");

  if (dataEntrada && !dataEntrada.value) {
    const hoje = new Date().toISOString().split("T")[0];
    dataEntrada.value = hoje;
  }

  atualizarPreview();
});

function atualizarPreview() {
  const codigo = document.getElementById("codigo")?.value || "MP-0000";
  const descricao = document.getElementById("descricao")?.value || "Nova matéria-prima";
  const lote = document.getElementById("lote")?.value || "—";
  const quantidade = document.getElementById("quantidade")?.value || "—";
  const unidade = document.getElementById("unidade")?.value || "";
  const localizacao = document.getElementById("localizacao")?.value || "—";

  document.getElementById("previewCodigo").textContent = codigo;
  document.getElementById("previewDescricao").textContent = descricao;
  document.getElementById("previewTexto").textContent = "Material preparado para identificação, conferência e rastreabilidade por QR Code.";
  document.getElementById("previewLote").textContent = "Lote: " + lote;
  document.getElementById("previewQtd").textContent = "Quantidade: " + quantidade + " " + unidade;
  document.getElementById("previewLocal").textContent = "Local: " + localizacao;
}

function limparFormulario() {
  const form = document.getElementById("materialForm");
  const dataEntrada = document.getElementById("dataEntrada");

  if (form) {
    form.reset();
  }

  if (dataEntrada) {
    dataEntrada.value = new Date().toISOString().split("T")[0];
  }

  atualizarPreview();
}