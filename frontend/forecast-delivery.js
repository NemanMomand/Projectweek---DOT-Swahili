const enabledInput = document.getElementById("delivery-enabled");
const testPhoneInput = document.getElementById("test-phone");
const saveButton = document.getElementById("save-settings");
const sendNowButton = document.getElementById("send-now");
const refreshButton = document.getElementById("refresh");
const statusLine = document.getElementById("settings-status");
const lastSentLine = document.getElementById("last-sent");

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function renderSettings(settings) {
  enabledInput.checked = !!settings.enabled;
  lastSentLine.textContent = settings.last_sent_date_utc
    ? `Last successful daily send (UTC): ${settings.last_sent_date_utc}`
    : "No successful daily send recorded yet.";
}

async function loadSettings(options = {}) {
  const { silent = false } = options;
  if (!silent) {
    statusLine.textContent = "Loading delivery setting...";
  }
  try {
    const settings = await api("/api/v1/forecast-delivery/settings");
    renderSettings(settings);
    if (!silent) {
      statusLine.textContent = "Settings loaded.";
    }
  } catch (error) {
    statusLine.textContent = error.message;
  }
}

async function saveSettings() {
  statusLine.textContent = "Saving...";
  try {
    const settings = await api("/api/v1/forecast-delivery/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: enabledInput.checked }),
    });
    renderSettings(settings);
    statusLine.textContent = settings.enabled
      ? "Daily tomorrow-forecast SMS is enabled."
      : "Daily tomorrow-forecast SMS is disabled.";
  } catch (error) {
    statusLine.textContent = error.message;
  }
}

async function sendNow() {
  statusLine.textContent = "Sending now...";
  try {
    const phone = testPhoneInput.value.trim();
    const query = phone
      ? `/api/v1/forecast-delivery/dispatch-now?phone_number=${encodeURIComponent(phone)}&language=en`
      : "/api/v1/forecast-delivery/dispatch-now?force=true";
    const result = await api(query, { method: "POST" });
    const sent = result.sent ?? 0;
    const skipped = result.skipped ?? 0;
    const base = `Dispatch result: ${result.status || "unknown"}. Sent: ${sent}, skipped: ${skipped}.`;
    statusLine.textContent = result.error ? `${base} Reason: ${result.error}` : base;
    await loadSettings({ silent: true });
  } catch (error) {
    statusLine.textContent = error.message;
  }
}

saveButton.addEventListener("click", saveSettings);
sendNowButton.addEventListener("click", sendNow);
refreshButton.addEventListener("click", loadSettings);

loadSettings();
