const NAV_ITEMS = [
  { key: "messages-live", label: "Live Messages", href: "/messages-live" },
  { key: "rain-live", label: "Live Weather", href: "/mvua-live" },
  { key: "forecast-delivery", label: "Forecast SMS", href: "/forecast-delivery" },
];

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

  const navMarkup = `
    <nav class="topnav" aria-label="Primary">
      <a class="brand" href="/messages-live">Dot Swahili</a>
      <div class="topnav-links">${links}</div>
    </nav>
  `;

  shell.insertAdjacentHTML("afterbegin", navMarkup);
}

renderTopNav();
