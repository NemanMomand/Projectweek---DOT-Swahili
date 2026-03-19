async function api(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json();
}

const THRESHOLD_COUNT = 2;
// Each signal has one English (en) and one Swahili (sw) text.
// Both are sent per click so the threshold of 2 is reached immediately.
const DEMO_SIGNAL_TEXTS = {
  storm:   { en: "there is a big storm coming right now",       sw: "dhoruba inakuja sasa" },
  rain:    { en: "heavy rain is falling on the farm today",     sw: "mvua nyingi sana leo" },
  drought: { en: "severe drought on the farm, no rain at all",  sw: "ukame mkubwa shambani" },
  heat:    { en: "extremely hot weather today on the farm",     sw: "joto kali sana leo" },
};

function typeClass(type) {
  return String(type).toLowerCase().replace(/_/g, "-");
}

function cardLine(label, value) {
  return `<div class="meta"><strong>${label}:</strong> ${value ?? "-"}</div>`;
}

function formatDate(dt) {
  if (!dt) return "-";
  return new Date(dt).toLocaleString();
}

function setDemoStatus(message, isError = false) {
  const el = document.getElementById("demo-status");
  if (!el) return;
  el.textContent = message;
  el.style.color = isError ? "#b91c1c" : "var(--muted, #64748b)";
}

function getTargetPhone() {
  const input = document.getElementById("target-phone");
  const phone = (input?.value || "").trim();
  if (!phone.startsWith("+") || phone.length < 9) {
    throw new Error("Gebruik een geldig nummer in E.164 formaat, bv +32470770258");
  }
  return phone;
}

async function ensureFarmerForPhone(phone, signal) {
  const farmers = await api("/api/v1/farmers");
  const existing = farmers.find((f) => f.phone_number === phone);
  if (existing) return phone;

  const stamp = Date.now().toString().slice(-6);
  const payload = {
    full_name: `Demo ${signal.toUpperCase()} ${stamp}`,
    phone_number: phone,
    preferred_language: "sw",
    region: "Arusha",
    district: "Meru",
    village: "Usa River",
    latitude: -3.369,
    longitude: 36.8569,
    crop_type: "Maize",
    is_active: true,
  };

  const res = await fetch("/api/v1/farmers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Farmer create failed (${res.status})`);
  }
  return phone;
}

async function sendInbound(phone, body, sid) {
  const payload = {
    phone_number: phone,
    body,
    provider_message_id: sid,
    raw_payload: {
      source: "feedback-groups-demo",
      provider: "ui",
    },
  };

  const res = await fetch("/api/v1/sms/reply", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-webhook-token": "local-webhook-token",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Inbound failed (${res.status})`);
  }
}

async function triggerDemoSignal(signal) {
  const texts = DEMO_SIGNAL_TEXTS[signal];
  if (!texts) {
    throw new Error(`Unsupported signal: ${signal}`);
  }

  setDemoStatus(`Bezig: ${signal.toUpperCase()} trigger voorbereiden...`);
  const phone = getTargetPhone();
  await ensureFarmerForPhone(phone, signal);

  const ts = Date.now();
  // Send English message first
  await sendInbound(phone, texts.en, `ui-${signal}-${ts}-en`);
  // Send Swahili message second — this hits threshold=2 and triggers the alert
  await sendInbound(phone, texts.sw, `ui-${signal}-${ts}-sw`);

  await sendCallThenSms(phone, signal);

  setDemoStatus(
    `2x ${signal.toUpperCase()} verstuurd (EN + SW) -> call gestart en daarna sms verstuurd naar ${phone}.`
  );
}

async function sendCallThenSms(phone, signal) {
  const signalName = String(signal || "alert").toUpperCase();
  const payload = {
    phone_number: phone,
    message_en: `Dot Swahili voice alert. ${signalName} risk has been detected for your farm area.`,
    message_sw: `Tahadhari ya Dot Swahili kwa sauti. Hatari ya ${signalName} imegunduliwa kwa eneo lako la shamba.`,
    sms_body: `DOT Swahili: ${signalName} warning activated for your area.`,
    delay_seconds: 8,
  };
  const res = await fetch("/api/v1/voice/call-then-sms", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = data?.detail || data?.message || "";
    } catch {
      detail = "";
    }
    throw new Error(detail ? `Call+SMS failed (${res.status}): ${detail}` : `Call+SMS failed (${res.status})`);
  }
  return res.json();
}

async function sendDirectSms(phone, body) {
  const payload = {
    phone_number: phone,
    body,
  };
  const res = await fetch("/api/v1/sms/send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const data = await res.json();
      detail = data?.detail || data?.message || "";
    } catch {
      detail = "";
    }
    throw new Error(detail ? `Direct SMS failed (${res.status}): ${detail}` : `Direct SMS failed (${res.status})`);
  }
}

async function sendTestSmsToTarget() {
  const phone = getTargetPhone();
  await sendDirectSms(phone, "DOT Swahili testbericht: SMS-koppeling werkt.");
  setDemoStatus(`Test SMS verstuurd naar ${phone}.`);
}

function renderSummary(grouped) {
  const container = document.getElementById("summary-tiles");
  if (!Object.keys(grouped).length) {
    container.innerHTML = "<p class='meta'>No feedback received yet.</p>";
    return;
  }
  container.innerHTML = Object.entries(grouped)
    .sort((a, b) => b[1].length - a[1].length)
    .map(([type, items]) => `
      <div class="summary-tile">
        <div class="tile-count">${items.length}</div>
        <div class="type-badge ${typeClass(type)}">${type}</div>
        <div class="tile-label">replies</div>
      </div>
    `)
    .join("");
}

function renderGroups(grouped) {
  const container = document.getElementById("groups-list");
  const entries = Object.entries(grouped).sort((a, b) => b[1].length - a[1].length);

  if (!entries.length) {
    container.innerHTML = "<p class='meta'>No AI-classified feedback found. Farmer replies are classified when they arrive via inbound SMS.</p>";
    return;
  }

  container.innerHTML = entries.map(([type, items]) => `
    <div style="margin-bottom:1.5rem">
      <div class="group-header">
        <span class="group-count">${items.length}</span>
        <span class="type-badge ${typeClass(type)}">${type}</span>
        <span class="meta" style="margin:0">replies classified as <strong>${type}</strong></span>
      </div>
      ${items.map(item => `
        <div class="data-card">
          <div class="data-top">
            <strong>"${item.free_text}"</strong>
            <span class="badge completed">${item.parsed_language ?? "?"}</span>
          </div>
          ${cardLine("Farmer ID", item.farmer_id ?? "unknown")}
          ${item.intensity != null ? cardLine("Intensity", item.intensity + "/5") : ""}
          ${item.latitude != null ? cardLine("Location", `${item.latitude?.toFixed(3)}, ${item.longitude?.toFixed(3)}`) : ""}
          ${cardLine("Received", formatDate(item.created_at))}
        </div>
      `).join("")}
    </div>
  `).join("<hr style='margin:1.5rem 0;border:none;border-top:1px solid var(--border,#e2e8f0)'>");
}

function renderAlerts(alerts) {
  const container = document.getElementById("alerts-list");
  // Filter to alerts that were triggered by feedback signal (AlertType: rain, heat, storm, drought)
  const feedbackTriggered = alerts.filter(a =>
    ["rain", "heat", "storm", "drought"].includes(String(a.alert_type).toLowerCase())
  );

  if (!feedbackTriggered.length) {
    container.innerHTML = `
      <p class="meta">
        No threshold-triggered alerts yet. An alert is sent automatically when the same feedback type
        (e.g. RAIN) is received <strong>2 or more times</strong> within the configured time window
        from the same farmer.
      </p>
    `;
    return;
  }

  container.innerHTML = feedbackTriggered
    .sort((a, b) => new Date(b.scheduled_for) - new Date(a.scheduled_for))
    .map(alert => `
      <div class="data-card">
        <div class="data-top">
          <strong>${alert.alert_type}</strong>
          <span class="badge ${alert.delivery_status === "sent" ? "completed" : "pending"}">${alert.delivery_status}</span>
        </div>
        ${cardLine("Severity", alert.severity)}
        ${cardLine("Triggered at", formatDate(alert.scheduled_for))}
        ${cardLine("SMS sent at", alert.sent_at ? formatDate(alert.sent_at) : "not yet sent")}
        ${alert.message ? cardLine("Message", `<em>${alert.message}</em>`) : ""}
        <div class="alert-triggered">
          ⚡ Triggered because the same signal was received 2+ times within the time window
        </div>
      </div>
    `)
    .join("");
}

async function load() {
  try {
    const [feedback, alerts] = await Promise.all([
      api("/api/v1/feedback"),
      api("/api/v1/messages/alerts?real_only=true").catch(() => []),
    ]);

    // Group feedback by type
    const grouped = {};
    for (const item of feedback) {
      const t = item.feedback_type;
      if (!grouped[t]) grouped[t] = [];
      grouped[t].push(item);
    }

    renderSummary(grouped);
    renderGroups(grouped);
    renderAlerts(alerts);
  } catch (err) {
    const msg = `<p class="meta" style="color:red">Error loading data: ${err.message}</p>`;
    document.getElementById("summary-tiles").innerHTML = msg;
    document.getElementById("groups-list").innerHTML = msg;
    document.getElementById("alerts-list").innerHTML = msg;
  }
}

document.getElementById("refresh").addEventListener("click", load);

document.querySelectorAll(".demo-trigger").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const signal = btn.getAttribute("data-signal");
    const oldText = btn.textContent;
    btn.disabled = true;
    btn.textContent = "Sending...";
    try {
      await triggerDemoSignal(signal);
      await load();
    } catch (err) {
      setDemoStatus(`Fout bij triggeren: ${err.message}`, true);
    } finally {
      btn.disabled = false;
      btn.textContent = oldText;
    }
  });
});

const testBtn = document.getElementById("send-test-sms");
if (testBtn) {
  testBtn.addEventListener("click", async () => {
    const oldText = testBtn.textContent;
    testBtn.disabled = true;
    testBtn.textContent = "Sending...";
    try {
      await sendTestSmsToTarget();
      await load();
    } catch (err) {
      setDemoStatus(`Fout bij test SMS: ${err.message}`, true);
    } finally {
      testBtn.disabled = false;
      testBtn.textContent = oldText;
    }
  });
}

load();
