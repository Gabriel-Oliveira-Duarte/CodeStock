(function () {
  function iniciarSidebarResponsiva() {
    const botao = document.getElementById("sidebarMobileToggle");
    const overlay = document.getElementById("sidebarOverlay");
    const sidebar = document.getElementById("sidebar");

    if (!botao || !overlay || !sidebar) return;

    let scrollAtual = 0;

    function travarPagina() {
      scrollAtual = window.scrollY || document.documentElement.scrollTop || 0;
      document.body.style.top = `-${scrollAtual}px`;
      document.body.classList.add("sidebar-open");
    }

    function destravarPagina() {
      document.body.classList.remove("sidebar-open");
      document.body.style.top = "";
      window.scrollTo(0, scrollAtual);
    }

    function abrirSidebar() {
      travarPagina();
      botao.setAttribute("aria-expanded", "true");
    }

    function fecharSidebar() {
      destravarPagina();
      botao.setAttribute("aria-expanded", "false");
    }

    botao.addEventListener("click", function () {
      if (document.body.classList.contains("sidebar-open")) {
        fecharSidebar();
      } else {
        abrirSidebar();
      }
    });

    overlay.addEventListener("click", fecharSidebar);

    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth <= 1180) {
          fecharSidebar();
        }
      });
    });

    window.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && document.body.classList.contains("sidebar-open")) {
        fecharSidebar();
      }
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 1180 && document.body.classList.contains("sidebar-open")) {
        fecharSidebar();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciarSidebarResponsiva);
  } else {
    iniciarSidebarResponsiva();
  }
})();
