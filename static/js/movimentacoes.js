const hoje = new Date().toISOString().split("T")[0];
    document.getElementById("data").value = hoje;

    document.getElementById("movimentacaoForm").addEventListener("submit", function(event) {
      event.preventDefault();
      document.getElementById("successMessage").classList.add("show");
    });

    function limparFormulario() {
      document.getElementById("movimentacaoForm").reset();
      document.getElementById("data").value = hoje;
      document.getElementById("successMessage").classList.remove("show");
    }

    function filtrarTabela() {
      const busca = document.getElementById("busca").value.toLowerCase();
      const tipo = document.getElementById("tipoFiltro").value.toLowerCase();
      const linhas = document.querySelectorAll("#movTabela tbody tr");
      linhas.forEach(linha => {
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
