function filtrarTabela() {
  const busca = document.getElementById("busca").value.toLowerCase();
  const status = document.getElementById("statusFiltro").value.toLowerCase();
  const local = document.getElementById("localFiltro").value.toLowerCase();
  const fornecedor = document.getElementById("fornecedorFiltro").value.toLowerCase();

  const linhas = document.querySelectorAll("#materiaisTabela tbody tr");

  linhas.forEach((linha) => {
    const texto = linha.innerText.toLowerCase();

    const combinaBusca = texto.includes(busca);
    const combinaStatus = status === "" || texto.includes(status);
    const combinaLocal = local === "" || texto.includes(local);
    const combinaFornecedor = fornecedor === "" || texto.includes(fornecedor);

    linha.style.display = combinaBusca && combinaStatus && combinaLocal && combinaFornecedor ? "" : "none";
  });
}

function limparFiltros() {
  document.getElementById("busca").value = "";
  document.getElementById("statusFiltro").value = "";
  document.getElementById("localFiltro").value = "";
  document.getElementById("fornecedorFiltro").value = "";
  filtrarTabela();
}