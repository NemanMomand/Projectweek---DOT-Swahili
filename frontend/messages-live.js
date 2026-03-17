const messageForm = document.getElementById("filter-form");
const alertsContainer = document.getElementById("alerts-list");
const smsContainer = document.getElementById("sms-list");
const repliesContainer = document.getElementById("replies-list");
const statusMessage = document.getElementById("filter-message");
const refreshButton = document.getElementById("refresh");
const opsKpis = document.getElementById("ops-kpis");

async function api(path, tolerateNotFound = false) {
  const response = await fetch(path);
  if (response.status === 404 && tolerateNotFound) {
    return [];
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

function cardLine(label, value) {
  return `<div class="meta"><strong>${label}:</strong> ${value ?? "-"}</div>`;
}

function isTestRecord(item) {
  const providerId = String(item.provider_message_id || "").toLowerCase();
  const body = String(item.body || "").toLowerCase();
  return providerId.includes("localtest") || body.includes("test");
}

function renderAlerts(items) {
  if (!items.length) {
    alertsContainer.innerHTML = "<p class='meta'>No real alerts found for this filter.</p>";
    return;
  }

  alertsContainer.innerHTML = items
    .map(
      (item) => `
      <div class="data-card">
        <div class="data-top">
          <strong>${item.alert_type}</strong>
          <span class="badge ${item.delivery_status === "sent" ? "completed" : "pending"}">${item.delivery_status}</span>
        </div>
        ${cardLine("Severity", item.severity)}
        ${cardLine("Scheduled", new Date(item.scheduled_for).toLocaleString())}
        ${cardLine("Sent", item.sent_at ? new Date(item.sent_at).toLocaleString() : "not yet")}
        ${cardLine("Message", item.message)}
      </div>
    `
    )
    .join("");
}

function renderSms(items) {
  if (!items.length) {
    smsContainer.innerHTML = "<p class='meta'>No real SMS messages found.</p>";
    return;
  }

  smsContainer.innerHTML = items
    .map(
      (item) => `
      <div class="data-card">
        <div class="data-top">
          <strong>SMS</strong>
          <span class="badge ${item.status === "sent" || item.status === "delivered" ? "completed" : "pending"}">${item.status}</span>
        </div>
        ${cardLine("Phone", item.phone_number)}
        ${cardLine("Provider ID", item.provider_message_id || "-")}
        ${cardLine("Time", item.sent_at ? new Date(item.sent_at).toLocaleString() : new Date(item.created_at).toLocaleString())}
        ${cardLine("Body", item.body)}
      </div>
    `
    )
    .join("");
}

function renderReplies(items) {
  if (!items.length) {
    repliesContainer.innerHTML = "<p class='meta'>No real inbound replies found.</p>";
    return;
  }

  repliesContainer.innerHTML = items
    .map(
      (item) => `
      <div class="data-card">
        <div class="data-top">
          <strong>Reply</strong>
          <span class="badge completed">${item.status}</span>
        </div>
        ${cardLine("Phone", item.phone_number)}
        ${cardLine("Received", item.received_at ? new Date(item.received_at).toLocaleString() : "-")}
        ${cardLine("Body", item.body)}
      </div>
    `
    )
    .join("");
}

function renderKpis(alerts, sms, replies) {
  if (!opsKpis) return;

  const times = [];
  for (const item of alerts) {
    if (item.sent_at) times.push(new Date(item.sent_at));
    if (item.scheduled_for) times.push(new Date(item.scheduled_for));
  }
  for (const item of sms) {
    if (item.sent_at) times.push(new Date(item.sent_at));
    if (item.created_at) times.push(new Date(item.created_at));
  }
  for (const item of replies) {
    if (item.received_at) times.push(new Date(item.received_at));
    if (item.created_at) times.push(new Date(item.created_at));
  }

  const lastActivity = times.length
    ? new Date(Math.max(...times.map((t) => t.getTime()))).toLocaleString()
    : "No activity";

  opsKpis.innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Alerts</div>
      <div class="kpi-value">${alerts.length}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Outbound SMS</div>
      <div class="kpi-value">${sms.length}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Inbound Replies</div>
      <div class="kpi-value">${replies.length}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Last Activity</div>
      <div class="kpi-value">${lastActivity}</div>
    </div>
  `;
}

async function loadMessages(phoneNumber) {
  statusMessage.textContent = "Loading real message data...";
  const query = phoneNumber ? `?phone_number=${encodeURIComponent(phoneNumber)}&real_only=true` : "?real_only=true";

  try {
    const [alertsResult, smsResult, repliesResult] = await Promise.allSettled([
      api(`/api/v1/messages/alerts${query}`, true),
      api(`/api/v1/messages/sms${query}`),
      api(`/api/v1/messages/replies${query}`),
    ]);

    const alertsRaw = alertsResult.status === "fulfilled" ? alertsResult.value : [];
    const smsRaw = smsResult.status === "fulfilled" ? smsResult.value : [];
    const repliesRaw = repliesResult.status === "fulfilled" ? repliesResult.value : [];

    const alerts = alertsRaw.filter((item) => !isTestRecord(item));
    const sms = smsRaw.filter((item) => !isTestRecord(item));
    const replies = repliesRaw.filter((item) => !isTestRecord(item));

    renderKpis(alerts, sms, replies);
    renderAlerts(alerts);
    renderSms(sms);
    renderReplies(replies);

    const failed = [];
    if (alertsResult.status === "rejected") failed.push("alerts");
    if (smsResult.status === "rejected") failed.push("sms");
    if (repliesResult.status === "rejected") failed.push("replies");

    if (failed.length) {
      statusMessage.textContent = `Partial data loaded. Failed: ${failed.join(", ")} (backend may be down).`;
      if (alertsResult.status === "rejected") {
        alertsContainer.innerHTML = "<p class='meta'>Alerts unavailable right now (API error).</p>";
      }
      if (smsResult.status === "rejected") {
        smsContainer.innerHTML = "<p class='meta'>SMS unavailable right now (API error).</p>";
      }
      if (repliesResult.status === "rejected") {
        repliesContainer.innerHTML = "<p class='meta'>Replies unavailable right now (API error).</p>";
      }
      return;
    }

    statusMessage.textContent = "Real message dashboard updated.";
  } catch (error) {
    statusMessage.textContent = `Backend/API unreachable: ${error.message}`;
    renderKpis([], [], []);
    alertsContainer.innerHTML = "<p class='meta'>Alerts unavailable right now (API unreachable).</p>";
    smsContainer.innerHTML = "<p class='meta'>SMS unavailable right now (API unreachable).</p>";
    repliesContainer.innerHTML = "<p class='meta'>Replies unavailable right now (API unreachable).</p>";
  }
}

messageForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const phone = messageForm.elements.phone_number.value.trim();
  loadMessages(phone);
});

if (refreshButton) {
  refreshButton.addEventListener("click", () => {
    const phone = messageForm.elements.phone_number.value.trim();
    loadMessages(phone);
  });
}

loadMessages("");
