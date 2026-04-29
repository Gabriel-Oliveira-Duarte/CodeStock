const empresaScreen = document.getElementById("empresaScreen");
const usuarioScreen = document.getElementById("usuarioScreen");
const pillEmpresa = document.getElementById("pillEmpresa");
const pillUsuario = document.getElementById("pillUsuario");
const voltarEmpresa = document.getElementById("voltarEmpresa");

function mostrarEmpresa() {
  if (!empresaScreen || !usuarioScreen || !pillEmpresa || !pillUsuario) return;

  usuarioScreen.classList.remove("active");
  empresaScreen.classList.add("active");

  pillUsuario.classList.remove("active");
  pillEmpresa.classList.add("active");
}

function mostrarUsuario() {
  if (!empresaScreen || !usuarioScreen || !pillEmpresa || !pillUsuario) return;

  empresaScreen.classList.remove("active");
  usuarioScreen.classList.add("active");

  pillEmpresa.classList.remove("active");
  pillUsuario.classList.add("active");
}

document.addEventListener("DOMContentLoaded", function () {
  if (!empresaScreen || !usuarioScreen) return;

  if (usuarioScreen.classList.contains("active")) {
    mostrarUsuario();
  } else {
    mostrarEmpresa();
  }
});

if (voltarEmpresa) {
  voltarEmpresa.addEventListener("click", function () {
    window.location.href = "/login";
  });
}