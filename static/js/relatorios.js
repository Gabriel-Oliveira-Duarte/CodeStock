function alternarMenu() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) sidebar.classList.toggle("open");
}

document.querySelectorAll(".menu a, .logout").forEach((link) => {
  link.addEventListener("click", () => {
    const sidebar = document.getElementById("sidebar");
    if (sidebar && window.innerWidth <= 900) {
      sidebar.classList.remove("open");
    }
  });
});

function filtrarTabela() {
  const busca = (document.getElementById("buscaTabela")?.value || "").toLowerCase();
  const status = (document.getElementById("statusFiltro")?.value || "").toLowerCase();
  const linhas = document.querySelectorAll("#relatoriosTabela tbody tr");

  linhas.forEach((linha) => {
    const texto = linha.innerText.toLowerCase();
    const combinaBusca = texto.includes(busca);
    const combinaStatus = status === "" || texto.includes(status);
    linha.style.display = combinaBusca && combinaStatus ? "" : "none";
  });
}

function limparTabela() {
  const busca = document.getElementById("buscaTabela");
  const status = document.getElementById("statusFiltro");
  if (busca) busca.value = "";
  if (status) status.value = "";
  filtrarTabela();
}

function obterQueryFiltros(extra = {}) {
  const form = document.querySelector(".filters-panel");
  const params = new URLSearchParams();

  if (form) {
    const dados = new FormData(form);
    dados.forEach((valor, chave) => {
      if (valor !== null && String(valor).trim() !== "") {
        params.set(chave, valor);
      }
    });
  }

  Object.entries(extra).forEach(([chave, valor]) => {
    if (valor === null || valor === undefined || valor === "") {
      params.delete(chave);
    } else {
      params.set(chave, valor);
    }
  });

  return params.toString();
}

function exportarRelatorio(urlBase) {
  const query = obterQueryFiltros();
  window.location.href = query ? `${urlBase}?${query}` : urlBase;
}

function imprimirRelatorio(urlBase) {
  const query = obterQueryFiltros({ imprimir: "1" });
  window.location.href = query ? `${urlBase}?${query}` : `${urlBase}?imprimir=1`;
}

document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("imprimir") === "1") {
    setTimeout(() => window.print(), 450);
  }
});
