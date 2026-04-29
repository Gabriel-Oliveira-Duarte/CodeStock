const hoje = new Date().toISOString().split("T")[0];
    document.getElementById("dataEntrada").value = hoje;

    function atualizarPreview() {
      const codigo = document.getElementById("codigo").value || "MP-0000";
      const descricao = document.getElementById("descricao").value || "Nova matéria-prima";
      const lote = document.getElementById("lote").value || "—";
      const quantidade = document.getElementById("quantidade").value || "—";
      const unidade = document.getElementById("unidade").value || "";
      const localizacao = document.getElementById("localizacao").value || "—";

      document.getElementById("previewCodigo").textContent = codigo;
      document.getElementById("previewDescricao").textContent = descricao;
      document.getElementById("previewTexto").textContent = "Material preparado para identificação, conferência e rastreabilidade por QR Code.";
      document.getElementById("previewLote").textContent = "Lote: " + lote;
      document.getElementById("previewQtd").textContent = "Quantidade: " + quantidade + " " + unidade;
      document.getElementById("previewLocal").textContent = "Local: " + localizacao;
    }

    function limparFormulario() {
      document.getElementById("materialForm").reset();
      document.getElementById("dataEntrada").value = hoje;
      document.getElementById("successMessage").classList.remove("show");
      atualizarPreview();
    }

    document.getElementById("materialForm").addEventListener("submit", function(event) {
      event.preventDefault();
      document.getElementById("successMessage").classList.add("show");
    });