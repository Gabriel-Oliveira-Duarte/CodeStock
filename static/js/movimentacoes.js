document.addEventListener("DOMContentLoaded", function () {
  const data = document.getElementById("data");

  if (data && !data.value) {
    data.value = new Date().toISOString().split("T")[0];
  }
});

function limparFormulario() {
  const form = document.getElementById("movimentacaoForm");
  const data = document.getElementById("data");

  if (form) {
    form.reset();
  }

  if (data) {
    data.value = new Date().toISOString().split("T")[0];
  }
}

function filtrarTabela() {
  const busca = document.getElementById("busca").value.toLowerCase();
  const tipo = document.getElementById("tipoFiltro").value.toLowerCase();
  const linhas = document.querySelectorAll("#movTabela tbody tr");

  linhas.forEach((linha) => {
    const texto = linha.innerText.toLowerCase();
    const combinaBusca = texto.includes(busca);
    const combinaTipo = tipo === "" || texto.includes(tipo);

    linha.style.display = combinaBusca && combinaTipo ? "" : "none";
  });
}

function limparFiltros() {
  document.getElementById("busca").value = "";
  document.getElementById("tipoFiltro").value = "";
  filtrarTabela();
}