const NAV_ITEMS = [
  { key: "messages-live", label: "Live Messages", href: "/messages-live" },
  { key: "rain-live", label: "Live Weather", href: "/mvua-live" },
  { key: "forecast-delivery", label: "Forecast SMS", href: "/forecast-delivery" },
  { key: "feedback-groups", label: "AI Feedback Groups", href: "/feedback-groups" },
];

const THEME_KEY = "dotswahili-theme";

function applyTheme(theme) {
  const safeTheme = theme === "dark" ? "dark" : "light";
  document.body.setAttribute("data-theme", safeTheme);
  localStorage.setItem(THEME_KEY, safeTheme);

  const toggle = document.getElementById("theme-toggle");
  if (toggle) {
    toggle.textContent = safeTheme === "dark" ? "Light Theme" : "Dark Theme";
  }
}

function renderTopNav() {
  const shell = document.querySelector(".shell");
  if (!shell) {
    return;
  }

  const activePage = document.body.dataset.page || "";
  const links = NAV_ITEMS.map((item) => {
    const activeClass = item.key === activePage ? " active" : "";
    return `<a class="nav-link${activeClass}" href="${item.href}">${item.label}</a>`;
  }).join("");

  const now = new Date();
  const stamp = now.toLocaleString();

  const navMarkup = `
    <nav class="topnav" aria-label="Primary">
      <a class="brand" href="/messages-live">Dot Swahili <span aria-hidden="true">•</span> Live Ops</a>
      <div class="topnav-links">${links}</div>
      <div class="topnav-right">
        <button id="theme-toggle" class="theme-toggle" type="button">Dark Theme</button>
        <span class="pill" title="Last UI render time">${stamp}</span>
      </div>
    </nav>
  `;

  shell.insertAdjacentHTML("afterbegin", navMarkup);

  const savedTheme = localStorage.getItem(THEME_KEY) || "light";
  applyTheme(savedTheme);

  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const current = document.body.getAttribute("data-theme") || "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }
}

renderTopNav();
