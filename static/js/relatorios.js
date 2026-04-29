function alternarMenu() {
  const sidebar = document.getElementById("sidebar");
  sidebar.classList.toggle("open");
}

document.querySelectorAll(".menu a, .logout").forEach((link) => {
  link.addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    if (window.innerWidth <= 900) {
      sidebar.classList.remove("open");
    }
  });
});

function gerarRelatorio() {
  alert("Relatório gerado com sucesso. Esta ação pode ser conectada ao backend futuramente.");
}

function filtrarTabela() {
  const busca = document.getElementById("busca").value.toLowerCase();
  const status = document.getElementById("statusFiltro").value.toLowerCase();
  const linhas = document.querySelectorAll("#relatoriosTabela tbody tr");

  linhas.forEach((linha) => {
    const texto = linha.innerText.toLowerCase();
    const combinaBusca = texto.includes(busca);
    const combinaStatus = status === "" || texto.includes(status);
    linha.style.display = combinaBusca && combinaStatus ? "" : "none";
  });
}

function limparTabela() {
  document.getElementById("busca").value = "";
  document.getElementById("statusFiltro").value = "";
  filtrarTabela();
}
