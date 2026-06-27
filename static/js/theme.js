(function () {
  const STORAGE_KEY = "codestock-theme";

  function getSavedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY) || "light";
    } catch (error) {
      return "light";
    }
  }

  function saveTheme(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // Mantém o tema aplicado mesmo se o navegador bloquear localStorage.
    }
  }

  function updateButton(theme) {
    const button = document.getElementById("themeToggle");
    if (!button) return;

    button.textContent = theme === "dark" ? "Tema: Escuro" : "Tema: Claro";
    button.setAttribute("aria-label", theme === "dark" ? "Tema atual: escuro" : "Tema atual: claro");
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    updateButton(theme);
  }

  applyTheme(getSavedTheme());

  document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById("themeToggle");
    const currentTheme = getSavedTheme();

    applyTheme(currentTheme);

    if (!button) return;

    button.addEventListener("click", function () {
      const activeTheme = document.documentElement.getAttribute("data-theme") || "light";
      const newTheme = activeTheme === "dark" ? "light" : "dark";

      applyTheme(newTheme);
      saveTheme(newTheme);
    });
  });
})();
