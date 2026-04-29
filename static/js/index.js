let slideAtual = 0;

    function atualizarCarrossel() {
      const track = document.getElementById("fluxoTrack");
      const slides = document.querySelectorAll(".process-step");
      const dots = document.querySelectorAll(".carousel-dot");

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

      if (slideAtual < 0) {
        slideAtual = totalSlides - 1;
      }

      if (slideAtual >= totalSlides) {
        slideAtual = 0;
      }

      atualizarCarrossel();
    }

    function irParaSlide(index) {
      slideAtual = index;
      atualizarCarrossel();
    }

    // Scroll suave nos links internos: Início, Funcionalidades e Processo
    document.querySelectorAll('a[href^="#"]').forEach(link => {
      link.addEventListener("click", function(event) {
        const destino = document.querySelector(this.getAttribute("href"));

        if (destino) {
          event.preventDefault();
          destino.scrollIntoView({
            behavior: "smooth",
            block: "start"
          });
        }
      });
    });

    // Transição suave para links que abrem outras páginas, como cadastrar empresa e login
    document.querySelectorAll('a[href$=".html"]').forEach(link => {
      link.addEventListener("click", function(event) {
        const url = this.getAttribute("href");

        if (!url.startsWith("#")) {
          event.preventDefault();
          document.body.style.transition = "opacity 0.25s ease";
          document.body.style.opacity = "0";

          setTimeout(() => {
            window.location.href = url;
          }, 250);
        }
      });
    });