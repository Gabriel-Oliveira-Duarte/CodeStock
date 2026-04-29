const empresaForm = document.getElementById("empresaForm");
    const empresaScreen = document.getElementById("empresaScreen");
    const usuarioScreen = document.getElementById("usuarioScreen");
    const pillEmpresa = document.getElementById("pillEmpresa");
    const pillUsuario = document.getElementById("pillUsuario");
    const voltarEmpresa = document.getElementById("voltarEmpresa");
    const empresaSelecionada = document.getElementById("empresaSelecionada");

    empresaForm.addEventListener("submit", function(event) {
      event.preventDefault();

      const emailEmpresa = document.getElementById("emailEmpresa").value;
      const dominio = emailEmpresa.split("@")[1] || "empresa.com";
      empresaSelecionada.textContent = "Empresa vinculada a " + dominio;

      empresaScreen.classList.remove("active");
      usuarioScreen.classList.add("active");

      pillEmpresa.classList.remove("active");
      pillUsuario.classList.add("active");
    });

    voltarEmpresa.addEventListener("click", function() {
      usuarioScreen.classList.remove("active");
      empresaScreen.classList.add("active");

      pillUsuario.classList.remove("active");
      pillEmpresa.classList.add("active");
    });