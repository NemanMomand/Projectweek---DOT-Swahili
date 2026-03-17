const filterForm = document.getElementById("filter-form");
const regionSelect = document.getElementById("region");
const districtSelect = document.getElementById("district");
const villageSelect = document.getElementById("village");
const statusLine = document.getElementById("status");
const summaryContainer = document.getElementById("summary");
const summaryCardsContainer = document.getElementById("summary-cards");
const observationsList = document.getElementById("observations-list");
const weeklyChartCanvas = document.getElementById("weekly-chart");
const refreshButton = document.getElementById("refresh");
let weeklyChart;

async function api(path) {
  const response = await fetch(path);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function setOptions(select, values, placeholder) {
  const unique = [...new Set(values)].sort((a, b) => a.localeCompare(b));
  select.innerHTML = `<option value="">${placeholder}</option>` + unique.map((value) => `<option value="${value}">${value}</option>`).join("");
}

async function loadLocationFilters() {
  const farmers = await api("/api/v1/farmers");
  setOptions(regionSelect, farmers.map((f) => f.region), "All regions");
  setOptions(districtSelect, farmers.map((f) => f.district), "All districts");
  setOptions(villageSelect, farmers.map((f) => f.village), "All villages");
}

function renderSummary(items) {
  if (!items.length) {
    summaryContainer.innerHTML = "<p class='meta'>No real weather data for this filter.</p>";
    summaryCardsContainer.innerHTML = "";
    observationsList.innerHTML = "";
    return;
  }

  const totalRain = items.reduce((sum, item) => sum + item.rainfall_mm, 0);
  const avgTemp = items.reduce((sum, item) => sum + item.temperature_c, 0) / items.length;
  const avgHumidity = items.reduce((sum, item) => sum + item.humidity_pct, 0) / items.length;
  const maxWind = Math.max(...items.map((item) => item.wind_speed_kph));
  const stations = [...new Set(items.map((item) => item.station_name || item.station_id || "Unknown station"))];

  summaryCardsContainer.innerHTML = `
    <div class="metric-card">
      <div class="metric-label">Current Avg Temp</div>
      <div class="metric-value">${avgTemp.toFixed(1)} C</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Expected Rainfall</div>
      <div class="metric-value">${totalRain.toFixed(2)} mm</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Avg Humidity</div>
      <div class="metric-value">${avgHumidity.toFixed(1)}%</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Max Wind</div>
      <div class="metric-value">${maxWind.toFixed(1)} kph</div>
    </div>
  `;

  summaryContainer.innerHTML = `
    <div class="data-card">
      <div class="meta"><strong>Farmers in view:</strong> ${items.length}</div>
      <div class="meta"><strong>Total rainfall:</strong> ${totalRain.toFixed(2)} mm</div>
      <div class="meta"><strong>Average temperature:</strong> ${avgTemp.toFixed(1)} C</div>
      <div class="meta"><strong>Average humidity:</strong> ${avgHumidity.toFixed(1)}%</div>
      <div class="meta"><strong>Source:</strong> Visual Crossing (live API)</div>
      <div class="meta"><strong>Stations used:</strong> ${stations.join(", ")}</div>
    </div>
  `;
  observationsList.innerHTML = items
    .map(
      (item) => `
      <div class="data-card">
        <div class="data-top">
          <strong>${item.farmer_name}</strong>
          <span class="pill">${item.region} / ${item.district}</span>
        </div>
        <div class="meta"><strong>Village:</strong> ${item.village}</div>
        <div class="meta"><strong>Temperature:</strong> ${Number(item.temperature_c).toFixed(1)} C</div>
        <div class="meta"><strong>Rainfall:</strong> ${Number(item.rainfall_mm).toFixed(2)} mm</div>
        <div class="meta"><strong>Humidity:</strong> ${Number(item.humidity_pct).toFixed(1)}%</div>
        <div class="meta"><strong>Wind:</strong> ${Number(item.wind_speed_kph).toFixed(1)} kph</div>
        <div class="meta"><strong>Observed at:</strong> ${new Date(item.observed_at).toLocaleString()}</div>
        <div class="meta"><strong>Station:</strong> ${item.station_name || item.station_id || "Unknown"}</div>
      </div>
    `
    )
    .join("");
}

function renderWeeklyChart(points) {
  if (!weeklyChartCanvas) {
    return;
  }
  if (weeklyChart) {
    weeklyChart.destroy();
    weeklyChart = null;
  }
  if (!points.length) {
    return;
  }

  const labels = points.map((point) => point.date);
  const temperature = points.map((point) => Number(point.temp_c || 0));
  const rainfall = points.map((point) => Number(point.precip_mm || 0));

  weeklyChart = new Chart(weeklyChartCanvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          type: "line",
          label: "Temperature (C)",
          data: temperature,
          yAxisID: "yTemp",
          borderColor: "#d45b35",
          backgroundColor: "rgba(212,91,53,0.15)",
          tension: 0.28,
          borderWidth: 3,
          pointRadius: 3,
        },
        {
          label: "Rainfall (mm)",
          data: rainfall,
          yAxisID: "yRain",
          backgroundColor: "rgba(29,123,99,0.72)",
          borderColor: "rgba(24,50,38,0.9)",
          borderWidth: 1,
          borderRadius: 8,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
        },
      },
      scales: {
        yRain: {
          position: "left",
          beginAtZero: true,
          title: { display: true, text: "Rainfall (mm)" },
        },
        yTemp: {
          position: "right",
          grid: { drawOnChartArea: false },
          title: { display: true, text: "Temperature (C)" },
        },
      },
    },
  });
}

async function loadLiveWeather() {
  const params = new URLSearchParams();
  const region = regionSelect.value.trim();
  const district = districtSelect.value.trim();
  const village = villageSelect.value.trim();
  if (region) params.set("region", region);
  if (district) params.set("district", district);
  if (village) params.set("village", village);

  statusLine.textContent = "Loading real weather API data...";

  try {
    const items = await api(`/api/v1/weather/live/farmers?${params.toString()}`);
    renderSummary(items);

    try {
      const weekly = await api(`/api/v1/weather/live/weekly?${params.toString()}`);
      renderWeeklyChart(weekly);
      statusLine.textContent = `Loaded ${items.length} live weather points and weekly forecast.`;
    } catch (weeklyError) {
      if (weeklyChart) {
        weeklyChart.destroy();
        weeklyChart = null;
      }
      statusLine.textContent = `Loaded ${items.length} live weather points. Weekly forecast unavailable right now.`;
      console.warn("Weekly forecast unavailable", weeklyError);
    }
  } catch (error) {
    statusLine.textContent = error.message;
    summaryCardsContainer.innerHTML = "";
    observationsList.innerHTML = "";
    summaryContainer.innerHTML = "";
    if (weeklyChart) {
      weeklyChart.destroy();
      weeklyChart = null;
    }
  }
}

filterForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadLiveWeather();
});

if (refreshButton) {
  refreshButton.addEventListener("click", () => {
    loadLiveWeather();
  });
}

(async () => {
  try {
    await loadLocationFilters();
    await loadLiveWeather();
  } catch (error) {
    statusLine.textContent = error.message;
  }
})();
