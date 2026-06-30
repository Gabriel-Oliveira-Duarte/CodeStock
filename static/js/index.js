let slideAtual = 0;

function atualizarCarrossel() {
  const track = document.getElementById("fluxoTrack");
  const slides = document.querySelectorAll(".process-step");
  const dots = document.querySelectorAll(".carousel-dot");

  if (!track) return;

  track.style.transform = `translateX(-${slideAtual * 100}%)`;

  slides.forEach((slide, index) => {
    slide.classList.toggle("active", index === slideAtual);
  });

  dots.forEach((dot, index) => {
    dot.classList.toggle("active", index === slideAtual);
  });
}

function mudarSlide(direcao) {
  const totalSlides = document.querySelectorAll(".process-step").length;

  slideAtual += direcao;

  if (slideAtual < 0) slideAtual = totalSlides - 1;
  if (slideAtual >= totalSlides) slideAtual = 0;

  atualizarCarrossel();
}

function irParaSlide(index) {
  slideAtual = index;
  atualizarCarrossel();
}

document.addEventListener("DOMContentLoaded", function () {
  atualizarCarrossel();

  const menuBtn = document.getElementById("mobileMenuToggle");
  const closeBtn = document.getElementById("mobileMenuClose");
  const nav = document.getElementById("mainNav");
  const overlay = document.getElementById("mobileMenuOverlay");

  function abrirMenu() {
    if (!menuBtn || !nav || !overlay) return;

    document.body.classList.add("mobile-menu-open");
    menuBtn.setAttribute("aria-expanded", "true");
  }

  function fecharMenu() {
    if (!menuBtn || !nav || !overlay) return;

    document.body.classList.remove("mobile-menu-open");
    menuBtn.setAttribute("aria-expanded", "false");
  }

  function alternarMenu() {
    if (document.body.classList.contains("mobile-menu-open")) {
      fecharMenu();
    } else {
      abrirMenu();
    }
  }

  if (menuBtn) {
    menuBtn.addEventListener("click", alternarMenu);
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", fecharMenu);
  }

  if (overlay) {
    overlay.addEventListener("click", fecharMenu);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      fecharMenu();
    }
  });

  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener("click", function (event) {
      const destino = document.querySelector(this.getAttribute("href"));

      if (destino) {
        event.preventDefault();

        destino.scrollIntoView({
          behavior: "smooth",
          block: "start"
        });

        fecharMenu();
      }
    });
  });

  if (nav) {
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        fecharMenu();
      });
    });
  }
});
