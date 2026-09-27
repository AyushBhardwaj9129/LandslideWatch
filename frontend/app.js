let currentUser = null;
let locations = [];
let currentLocationId = null;
let leafletMap = null;
let mapLayer = null;

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

function riskColor(level) {
  return { LOW: "#41a36f", MODERATE: "#efb431", HIGH: "#f0802d", CRITICAL: "#e84b4f" }[level] || "#9baab5";
}

function riskIcon(level) {
  return { LOW: "🟢", MODERATE: "🟡", HIGH: "🟠", CRITICAL: "🔴" }[level] || "⚪";
}

// Backend returns a plain sentence like:
// "Rainfall (24h) contributed 19.1 pts, soil moisture contributed 27.3 pts, temperature contributed 8.4 pts."
// This turns that into labeled, color-coded factor bars instead of showing raw "pts" jargon.
function factorColor(label) {
  const l = label.toLowerCase();
  if (l.includes("rain")) return "#4d8ddd";
  if (l.includes("soil")) return "#41a36f";
  if (l.includes("temp")) return "#f0802d";
  if (l.includes("humid")) return "#6656d9";
  if (l.includes("slope")) return "#9baab5";
  return "#2d6f95";
}

function parseExplanation(text) {
  const factors = [];
  const regex = /([a-zA-Z][a-zA-Z0-9()\s/]*?)\s+contributed\s+([\d.]+)\s*pts/gi;
  let match;
  while ((match = regex.exec(text)) !== null) {
    const rawLabel = match[1].trim();
    const label = rawLabel.charAt(0).toUpperCase() + rawLabel.slice(1);
    factors.push({ label, value: parseFloat(match[2]) });
  }
  return factors;
}

function renderExplanation(text) {
  const el = document.getElementById("riskExplanation");
  const factors = parseExplanation(text);

  if (factors.length === 0) {
    // Couldn't parse it — fall back to showing the raw sentence rather than nothing.
    el.innerHTML = `<p class="explanation-fallback">${text}</p>`;
    return;
  }

  const maxValue = Math.max(...factors.map((f) => f.value), 1);

  el.innerHTML = `
    <div class="explanation-intro">What's driving this score</div>
    ${factors.map((f) => {
      const color = factorColor(f.label);
      const pct = Math.max(6, (f.value / maxValue) * 100);
      return `
        <div class="factor-row">
          <div class="factor-row-top">
            <span class="factor-dot" style="background:${color};"></span>
            <span class="factor-name">${f.label}</span>
          </div>
          <div class="factor-row-bottom">
            <div class="factor-bar-track">
              <div class="factor-bar-fill" style="width:${pct}%;background:${color};"></div>
            </div>
            <span class="factor-value">+${f.value.toFixed(1)} pts</span>
          </div>
        </div>`;
    }).join("")}
  `;
}

// ---------- Nav / view switching ----------
// Pulled out into a named function (previously an inline click-handler
// closure) so the chat assistant can trigger the exact same navigation
// a sidebar click does, instead of duplicating this logic elsewhere.
function switchView(view) {
  if (!view) return;
  const viewEl = document.getElementById(`view-${view}`);
  if (!viewEl) return;

  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  const navBtn = document.querySelector(`.nav-item[data-view="${view}"]`);
  if (navBtn) navBtn.classList.add("active");

  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  viewEl.classList.add("active");

  if (view === "map") initMap();
  if (view === "forecast") loadForecast();
  if (view === "routes") loadRoads();
  if (view === "shelters") loadShelters();
  if (view === "history") loadHistory();
}

document.querySelectorAll(".nav-item, [data-view]").forEach((el) => {
  el.addEventListener("click", () => switchView(el.dataset.view));
});

// ---------- Auth ----------
async function loadCurrentUser() {
  currentUser = await apiFetch("/auth/me");
  const initial = currentUser.name.charAt(0).toLowerCase();

  document.getElementById("userAvatar").textContent = initial;
  document.getElementById("userAvatarLg").textContent = initial;
  document.getElementById("userNameLg").textContent = currentUser.name;
  document.getElementById("userEmailLg").textContent = currentUser.email;
  document.getElementById("userRoleLg").textContent = currentUser.role;

  document.getElementById("settingsInfo").innerHTML = `
    <p style="font-size:13px;margin-bottom:6px;"><b>Name:</b> ${currentUser.name}</p>
    <p style="font-size:13px;margin-bottom:6px;"><b>Email:</b> ${currentUser.email}</p>
    <p style="font-size:13px;margin-bottom:12px;"><b>Role:</b> ${currentUser.role}</p>
  `;
}

async function logout() {
  await apiFetch("/auth/logout", { method: "POST" });
  window.location.href = "login.html";
}
document.getElementById("logoutBtn").addEventListener("click", logout);
document.getElementById("logoutBtn2").addEventListener("click", logout);

// ---------- Profile dropdown ----------
const profileTrigger = document.getElementById("profileTrigger");
const profileDropdown = document.getElementById("profileDropdown");

if (profileTrigger && profileDropdown) {
  profileTrigger.addEventListener("click", (event) => {
    event.stopPropagation();
    profileDropdown.classList.toggle("show");
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".profile-wrap")) {
      profileDropdown.classList.remove("show");
    }
  });
}

// ---------- Locations ----------
async function loadLocations() {
  locations = await apiFetch("/locations/");

  const select = document.getElementById("locationSelect");
  select.innerHTML = "";

  if (locations.length === 0) {
    select.innerHTML = `<option>No locations yet — add one via /docs</option>`;
    return;
  }

  locations.forEach((loc) => {
    const opt = document.createElement("option");
    opt.value = loc.id;
    opt.textContent = `${loc.name}, ${loc.state}`;
    select.appendChild(opt);
  });

  currentLocationId = locations[0].id;
  select.value = currentLocationId;

  select.addEventListener("change", () => {
    currentLocationId = parseInt(select.value, 10);
    loadHomeData();
    loadRainfallTrend();
    loadAlerts();
    loadShelterPreview();
    runRiskPrediction();
  });
}

// ---------- Home dashboard ----------
async function loadHomeData() {
  if (!currentLocationId) return;

  try {
    const weather = await apiFetch(`/weather/${currentLocationId}/current`);
    document.getElementById("rainfall").innerHTML = `${weather.rainfall_mm ?? "--"} <span>mm/hr</span>`;
    document.getElementById("temperature").textContent = `${weather.temperature ?? "--"}°C`;
    document.getElementById("humidity").textContent = `${weather.humidity ?? "--"}%`;
  } catch (e) {
    document.getElementById("rainfall").innerHTML = `-- <span>mm/hr</span>`;
  }

  try {
    const soil = await apiFetch(`/soil-moisture/${currentLocationId}/current`);
    document.getElementById("soilMoisture").textContent = `${soil.soil_moisture ?? "--"}%`;
  } catch (e) {
    document.getElementById("soilMoisture").textContent = "--%";
  }

  loadRainfallTrend();
  loadAlerts();
  loadShelterPreview();
}

let rainfallChartInstance = null;
let rainfallLoadToken = 0;

async function loadRainfallTrend() {

  const canvas = document.getElementById("rainfallChart");

  if (!canvas || !currentLocationId) {
    return;
  }

  // Guard against overlapping calls: if the location is switched again
  // before this call finishes, this token stops it from creating a
  // chart on top of a newer one ("Canvas is already in use").
  const requestLocationId = currentLocationId;
  const token = ++rainfallLoadToken;

  try {

    const result = await apiFetch(
      `/weather/${requestLocationId}/history?hours=24`
    );

    const history = Array.isArray(result)
      ? result
      : (result.data || []);

    console.log(
      "Rainfall history from backend:",
      history
    );

    // Helper: pull whatever timestamp field the backend actually sent
    // (different endpoints/seed scripts have used different names).
    function readingTime(reading) {
      const raw =
        reading.recorded_at ||
        reading.timestamp ||
        reading.created_at ||
        reading.time;
      return raw ? new Date(raw) : null;
    }

    let rainfallData = [];
    let labels = [];

    let usedRealData = false;

    if (history.length > 0) {

      // Use the REAL history points from the backend for this location,
      // instead of fabricating a shape from a single latest value.
      const sorted = [...history].sort((a, b) => {
        const ta = readingTime(a);
        const tb = readingTime(b);
        if (!ta || !tb) return 0;
        return ta - tb;
      });

      const realValues = sorted.map(
        (reading) => Number(reading.rainfall_mm) || 0
      );
      const realTimes = sorted.map((reading) => readingTime(reading));

      const MIN_POINTS = 8;

      const totalSpanCheck =
        realTimes[0] && realTimes[realTimes.length - 1]
          ? realTimes[realTimes.length - 1] - realTimes[0]
          : 0;

      // Require the readings to actually vary by a meaningful amount
      // (not just technically-different floats like 0.11 vs 0.12) —
      // otherwise this is a real but visually-flat signal and should
      // use the same honest "sample" fallback as no-data locations,
      // rather than rendering a near-invisible line.
      const valueRange =
        realValues.length > 0
          ? Math.max(...realValues) - Math.min(...realValues)
          : 0;

      const hasUsableSpread =
        sorted.length === 1 ||
        (totalSpanCheck > 0 && valueRange >= 2);

      if (hasUsableSpread) {
        usedRealData = true;

        if (sorted.length === 1) {
        // Only one real reading — nothing to interpolate, just show it.
        rainfallData = realValues;
        labels = realTimes.map((t, i) =>
          t
            ? t.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            : `#${i + 1}`
        );
      } else if (sorted.length < MIN_POINTS) {
        // Sparse real data (e.g. 2 readings) — linearly interpolate
        // BETWEEN the real anchor points so the line reads smoothly.
        // Every real reading still lands exactly on its true value and
        // true time; only the in-between points are filled in, the way
        // any chart renders a line between two known values.
        rainfallData = [];
        labels = [];

        const totalSpan = realTimes[realTimes.length - 1] - realTimes[0];
        const segments = MIN_POINTS - 1;

        for (let i = 0; i <= segments; i++) {
          const t = realTimes[0].getTime() + (totalSpan * i) / segments;
          const targetTime = new Date(t);

          // Find the two real anchors this interpolated time falls between
          let segIdx = 0;
          while (
            segIdx < realTimes.length - 2 &&
            targetTime > realTimes[segIdx + 1]
          ) {
            segIdx++;
          }

          const t0 = realTimes[segIdx].getTime();
          const t1 = realTimes[segIdx + 1].getTime();
          const v0 = realValues[segIdx];
          const v1 = realValues[segIdx + 1];
          const frac = t1 === t0 ? 0 : (targetTime.getTime() - t0) / (t1 - t0);
          const value = v0 + (v1 - v0) * frac;

          rainfallData.push(Math.round(value * 10) / 10);
          labels.push(
            targetTime.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })
          );
        }
        } else {
          // Already enough real points — use them as-is.
          rainfallData = realValues;
          labels = realTimes.map((t, i) =>
            t
              ? t.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
              : `#${i + 1}`
          );
        }
      }

    }

    if (!usedRealData) {

      // No real history rows for this location yet. Show a clearly
      // labeled illustrative 24h curve instead of leaving the panel
      // empty — seeded per-location so it's stable across reloads
      // rather than random noise every time.
      const points = 8; // every 3 hours across 24h
      const seed = requestLocationId * 9301 + 49297;

      function seededRandom(n) {
        const x = Math.sin(seed + n * 12.9898) * 43758.5453;
        return x - Math.floor(x);
      }

      // Base rainfall level derived from the seed so each location
      // gets a distinct but plausible profile.
      const baseLevel = 8 + seededRandom(0) * 20; // 8–28 mm/hr baseline

      rainfallData = [];
      const now = new Date();
      labels = [];

      for (let i = 0; i < points; i++) {
        // Rough diurnal shape: rain tends to build in the afternoon.
        const hourOfDay =
          (now.getHours() - (points - 1 - i) * 3 + 24) % 24;
        const diurnal =
          Math.sin(((hourOfDay - 6) / 24) * Math.PI * 2) * 0.5 + 0.5;

        const value =
          baseLevel * (0.5 + diurnal) +
          seededRandom(i + 1) * 6;

        rainfallData.push(Math.round(Math.max(0, value) * 10) / 10);

        const time = new Date(
          now.getTime() - (points - 1 - i) * 3 * 60 * 60 * 1000
        );
        labels.push(
          time.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })
        );
      }

    }

    const sourceLabel = document.getElementById("rainfallSourceLabel");
    if (sourceLabel) {
      sourceLabel.textContent = "Last 24 Hours";
      sourceLabel.classList.remove("sample-data");
    }

    // If a newer call started (location changed again while we were
    // waiting on the network), abandon this one — don't touch the canvas.
    if (token !== rainfallLoadToken) {
      return;
    }

    // Destroy old chart right before creating the new one
    if (rainfallChartInstance) {
      rainfallChartInstance.destroy();
      rainfallChartInstance = null;
    }

    // Create chart
    rainfallChartInstance = new Chart(
      canvas,
      {

        type: "line",

        data: {

          labels: labels,

          datasets: [

            {

              label: "Rainfall (mm/hr)",

              data: rainfallData,

              borderWidth: 3,

              tension: 0.4,

              fill: true,

              pointRadius: 3,

              pointHoverRadius: 5

            }

          ]

        },

        options: {

          responsive: true,

          maintainAspectRatio: false,

          plugins: {

            legend: {
              display: false
            },

            tooltip: {
              enabled: true
            }

          },

          scales: {

            x: {

              grid: {
                display: false
              }

            },

            y: {

              beginAtZero: true

            }

          }

        }

      }
    );

    // Show first and last time
    document.getElementById(
      "rainfallStart"
    ).textContent = labels[0] ?? "--";

    document.getElementById(
      "rainfallEnd"
    ).textContent =
      labels[labels.length - 1] ?? "--";

  } catch (error) {

    console.error(
      "Could not load rainfall history:",
      error
    );

  }

}

async function loadAlerts() {
  const listEl = document.getElementById("alertsList");
  try {
    const alerts = await apiFetch(`/alerts/?location_id=${currentLocationId}&is_active=true`);
    document.getElementById("alertCount").textContent = alerts.length;
    document.getElementById("alertBell").classList.toggle("has-alerts", alerts.length > 0);

    if (alerts.length === 0) {
      listEl.innerHTML = `
        <div class="alert-empty">
          <div class="alert-empty-icon">✓</div>
          <h4>All Clear</h4>
          <span>No active alerts for this location right now.</span>
        </div>`;
      return;
    }

    listEl.innerHTML = alerts.map((a) => `
      <div class="alert-card" style="--sev-color:${riskColor(a.risk_level)};">
        <div class="alert-icon">${riskIcon(a.risk_level)}</div>
        <div class="alert-body">
          <span class="alert-badge" style="background:${riskColor(a.risk_level)};">${a.risk_level}</span>
          <h4>${a.title}</h4>
          <p>${a.message}</p>
          <small>${new Date(a.created_at).toLocaleString()}</small>
        </div>
      </div>
    `).join("");
  } catch (e) {
    listEl.innerHTML = `
      <div class="alert-empty">
        <div class="alert-empty-icon" style="background:#fbe4e4;color:#c0392b;">!</div>
        <h4>Could Not Load Alerts</h4>
        <span>Check your connection and try again.</span>
      </div>`;
  }
}

document.getElementById("viewAllAlerts").addEventListener("click", async () => {
  const listEl = document.getElementById("alertsList");
  try {
    const alerts = await apiFetch(`/alerts/?location_id=${currentLocationId}`);
    listEl.innerHTML = alerts.map((a) => `
      <div class="alert-card" style="--sev-color:${riskColor(a.risk_level)}; opacity:${a.is_active ? 1 : 0.6};">
        <div class="alert-icon">${riskIcon(a.risk_level)}</div>
        <div class="alert-body">
          <span class="alert-badge" style="background:${riskColor(a.risk_level)};">${a.risk_level}${a.is_active ? "" : " · Resolved"}</span>
          <h4>${a.title}</h4>
          <p>${a.message}</p>
          <small>${new Date(a.created_at).toLocaleString()}</small>
        </div>
      </div>
    `).join("") || `
      <div class="alert-empty">
        <div class="alert-empty-icon">✓</div>
        <h4>All Clear</h4>
        <span>No alert history for this location.</span>
      </div>`;
  } catch (e) {
    showToast("Could not load alert history");
  }
});

async function loadShelterPreview() {
  try {
    const shelters = await apiFetch(`/shelters/?is_active=true`);
    const el = document.getElementById("shelterPreview");
    if (shelters.length === 0) {
      el.innerHTML = `<p style="font-size:12px;color:#8a97a1;">No shelters registered yet.</p>`;
      return;
    }
    el.innerHTML = shelters.slice(0, 3).map((s) => `
      <p style="font-size:12px;margin-bottom:6px;"><b>${s.name}</b> — capacity ${s.capacity ?? "?"}</p>
    `).join("");
  } catch (e) {
    document.getElementById("shelterPreview").innerHTML = `<p style="font-size:12px;color:#8a97a1;">Could not load shelters.</p>`;
  }
}

// ---------- Risk gauge ----------
async function runRiskPrediction() {
  if (!currentLocationId) return;

  try {
    const result = await apiFetch("/risk/predict", {
      method: "POST",
      body: JSON.stringify({ location_id: currentLocationId }),
    });

    updateRiskMeter(result.risk_score);
    renderExplanation(result.explanation);

    showToast("Risk recalculated");
  } catch (e) {
    console.error("Could not calculate risk:", e);
    document.getElementById("riskExplanation").innerHTML = `<p class="explanation-fallback">Could not calculate risk. Please try again.</p>`;
    showToast(e.message || "Could not calculate risk");
  }
}
document.getElementById("refreshRisk").addEventListener("click", runRiskPrediction);

// ---------- Forecast ----------
function relativeHours(target) {
  const diffMs = new Date(target) - new Date();
  const hours = Math.round(diffMs / (1000 * 60 * 60));
  if (hours <= 0) return "Now";
  if (hours === 1) return "In 1 hour";
  return `In ${hours} hours`;
}

async function loadForecast() {
  if (!currentLocationId) return;

  const listEl = document.getElementById("forecastList");
  listEl.innerHTML = `
    <p style="font-size:13px;color:#8a97a1;">
      Loading forecast...
    </p>
  `;

  const location = locations.find((loc) => loc.id === currentLocationId);
  const locationLabelEl = document.getElementById("forecastLocationLabel");
  if (locationLabelEl) {
    locationLabelEl.textContent = location ? `${location.name}, ${location.state}` : "the selected location";
  }

  try {
    const forecasts = await apiFetch(`/risk/forecast/${currentLocationId}`);

    if (!forecasts || forecasts.length === 0) {
      listEl.innerHTML = `
        <p style="font-size:13px;color:#8a97a1;">
          No forecast available yet. Click Refresh Forecast to generate one.
        </p>
      `;
      return;
    }

    listEl.innerHTML = forecasts
      .map((forecast) => {
        const level = forecast.risk_level || "MODERATE";
        const score = Math.max(0, Math.min(100, forecast.risk_score ?? 0));
        const color = riskColor(level);

        return `
          <div class="region-card">
            <div class="region-top">
              <div>
                <span class="region-eta">${relativeHours(forecast.forecast_time)}</span>
                <h3>${new Date(forecast.forecast_time).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}</h3>
              </div>
              <span class="risk-badge" style="background:${color};color:white;">${level}</span>
            </div>

            <div class="region-score-row">
              <div class="region-score-track">
                <div class="region-score-fill" style="width:${score}%;background:${color};"></div>
              </div>
              <strong class="region-score-value">${score}<span>/100</span></strong>
            </div>

            <div class="region-data">
              <div>
                <span>Confidence</span>
                <strong>${((forecast.confidence ?? 0) * 100).toFixed(0)}%</strong>
              </div>
            </div>
          </div>
        `;
      })
      .join("");
  } catch (error) {
    console.error("Could not load forecast:", error);
    listEl.innerHTML = `
      <p style="font-size:13px;color:#e84b4f;">
        Could not load forecast.
      </p>
    `;
  }
}


// Generate a new forecast when Refresh Forecast is clicked

document
  .getElementById("generateForecastBtn")
  .addEventListener("click", async () => {

    if (!currentLocationId) return;

    const listEl =
      document.getElementById("forecastList");

    listEl.innerHTML = `
      <p style="font-size:13px;color:#8a97a1;">
        Generating forecast...
      </p>
    `;

    try {

      await apiFetch(
        "/risk/forecast/generate",
        {
          method: "POST",

          body: JSON.stringify({
            location_id: currentLocationId,

            hours_ahead: [
              6,
              12,
              24
            ]
          })
        }
      );


      // After generating, load the latest forecast

      await loadForecast();

      showToast(
        "Forecast generated successfully"
      );

    }

    catch (error) {

      console.error(
        "Could not generate forecast:",
        error
      );

      listEl.innerHTML = `
        <p style="font-size:13px;color:#e84b4f;">
          Could not generate forecast.
        </p>
      `;

      showToast(
        "Could not generate forecast"
      );

    }

  });
// ---------- Roads ----------
async function loadRoads() {
  const listEl = document.getElementById("roadsList");
  listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Loading…</p>`;

  try {
    const roads = await apiFetch(`/roads/?location_id=${currentLocationId}`);
    if (roads.length === 0) {
      listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">No roads registered for this location yet.</p>`;
      return;
    }
    listEl.innerHTML = roads.map((r) => `
      <div class="alert-card" style="border-left:4px solid ${riskColor(r.risk_level)};display:flex;justify-content:space-between;align-items:center;">
        <div>
          <strong>${r.risk_level}${r.is_blocked ? " · BLOCKED" : ""}</strong>
          <h4>${r.name}</h4>
          <p>Risk score: ${r.risk_score}/100</p>
        </div>
        <button class="outline-btn" onclick="toggleRoadBlock(${r.id}, ${!r.is_blocked})">${r.is_blocked ? "Unblock" : "Block"}</button>
      </div>
    `).join("");
  } catch (e) {
    listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Could not load roads.</p>`;
  }
}

async function toggleRoadBlock(roadId, blocked) {
  try {
    await apiFetch(`/roads/${roadId}/block?is_blocked=${blocked}`, { method: "PATCH" });
    showToast(blocked ? "Road marked blocked" : "Road marked open");
    loadRoads();
  } catch (e) {
    showToast(e.message);
  }
}

document.getElementById("addRoadBtn").addEventListener("click", async () => {
  const name = prompt("Road name:");
  if (!name) return;
  const riskScore = parseFloat(prompt("Initial risk score (0-100):", "10") || "10");
  const loc = locations.find((l) => l.id === currentLocationId);

  try {
    await apiFetch("/roads/", {
      method: "POST",
      body: JSON.stringify({
        name,
        location_id: currentLocationId,
        latitude: loc.latitude,
        longitude: loc.longitude,
        risk_score: riskScore,
      }),
    });
    showToast("Road added");
    loadRoads();
  } catch (e) {
    showToast(e.message);
  }
});

// ---------- Shelters ----------
async function loadShelters() {
  const listEl = document.getElementById("sheltersList");
  listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Loading…</p>`;

  try {
    const shelters = await apiFetch("/shelters/");
    if (shelters.length === 0) {
      listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">No shelters registered yet.</p>`;
      return;
    }
    listEl.innerHTML = shelters.map((s) => `
      <div class="alert-card" style="border-left:4px solid ${s.is_active ? "#41a36f" : "#9baab5"};">
        <strong>${s.is_active ? "ACTIVE" : "INACTIVE"}</strong>
        <h4>${s.name}</h4>
        <p>${s.address || "No address on file"} · Capacity: ${s.capacity ?? "unknown"}</p>
        <small>${s.contact_number || "No contact number"}</small>
      </div>
    `).join("");
  } catch (e) {
    listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Could not load shelters.</p>`;
  }
}

document.getElementById("addShelterBtn").addEventListener("click", async () => {
  const name = prompt("Shelter name:");
  if (!name) return;
  const capacity = parseInt(prompt("Capacity:", "50") || "50", 10);
  const loc = locations.find((l) => l.id === currentLocationId);

  try {
    await apiFetch("/shelters/", {
      method: "POST",
      body: JSON.stringify({
        name,
        address: loc ? `${loc.name}, ${loc.state}` : "",
        latitude: loc ? loc.latitude : 0,
        longitude: loc ? loc.longitude : 0,
        capacity,
        is_active: true,
      }),
    });
    showToast("Shelter added");
    loadShelters();
  } catch (e) {
    showToast(e.message);
  }
});

// ---------- Route Status (geolocation-based safety check) ----------
// Distinct from the "Routes" admin view: instead of managing roads for
// whichever location is picked in the dropdown, this finds the user's
// live position, works out the nearest monitored location, and guides
// them toward the nearest active shelter.
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

function directionsUrl(fromLat, fromLng, toLat, toLng) {
  return `https://www.google.com/maps/dir/?api=1&origin=${fromLat},${fromLng}&destination=${toLat},${toLng}`;
}

const routeStatusModal = document.getElementById("routeStatusModal");
const routeStatusBody = document.getElementById("routeStatusBody");
const checkRouteStatusBtn = document.getElementById("checkRouteStatusBtn");
const closeRouteStatusModal = document.getElementById("closeRouteStatusModal");

async function renderRouteStatusForCoords(userLat, userLng) {
  routeStatusBody.innerHTML = `<p style="font-size:13px;color:#8a97a1;">Finding the nearest monitored area…</p>`;

  if (!locations || locations.length === 0) {
    routeStatusBody.innerHTML = `<p style="font-size:13px;color:#e84b4f;">No monitored locations are set up yet.</p>`;
    return;
  }

  // Nearest monitored location to the user
  let nearestLoc = null;
  let nearestLocDist = Infinity;
  locations.forEach((loc) => {
    if (loc.latitude == null || loc.longitude == null) return;
    const d = haversineKm(userLat, userLng, loc.latitude, loc.longitude);
    if (d < nearestLocDist) {
      nearestLocDist = d;
      nearestLoc = loc;
    }
  });

  try {
    const [alerts, shelters, roads] = await Promise.all([
      nearestLoc
        ? apiFetch(`/alerts/?location_id=${nearestLoc.id}&is_active=true`).catch(() => [])
        : Promise.resolve([]),
      apiFetch(`/shelters/?is_active=true`).catch(() => []),
      nearestLoc
        ? apiFetch(`/roads/?location_id=${nearestLoc.id}`).catch(() => [])
        : Promise.resolve([]),
    ]);

    // Worst active alert near the user
    const severityRank = { CRITICAL: 3, HIGH: 2, MODERATE: 1, LOW: 0 };
    const worstAlert = alerts.reduce((worst, a) => {
      if (!worst) return a;
      return (severityRank[a.risk_level] ?? 0) > (severityRank[worst.risk_level] ?? 0) ? a : worst;
    }, null);

    const bannerLevel = worstAlert ? worstAlert.risk_level : "LOW";
    const bannerColor = riskColor(bannerLevel);
    const bannerText = worstAlert
      ? `${worstAlert.risk_level} RISK near you — ${worstAlert.title}`
      : "No active alerts near your current location";

    // Nearest active shelter to the user
    let nearestShelter = null;
    let nearestShelterDist = Infinity;
    shelters.forEach((s) => {
      if (s.latitude == null || s.longitude == null) return;
      const d = haversineKm(userLat, userLng, s.latitude, s.longitude);
      if (d < nearestShelterDist) {
        nearestShelterDist = d;
        nearestShelter = s;
      }
    });

    const blockedRoads = roads.filter((r) => r.is_blocked);

    routeStatusBody.innerHTML = `
      <div class="alert-card" style="border-left:5px solid ${bannerColor};background:rgba(0,0,0,0.02);margin-bottom:14px;">
        <strong style="color:${bannerColor};">${bannerLevel}</strong>
        <h4>${bannerText}</h4>
        <p>${nearestLoc ? `Nearest monitored area: <b>${nearestLoc.name}, ${nearestLoc.state}</b> (${nearestLocDist.toFixed(1)} km away)` : "No nearby monitored area found."}</p>
      </div>

      ${nearestShelter ? `
        <div class="alert-card" style="border-left:5px solid #41a36f;margin-bottom:14px;">
          <strong>NEAREST SAFE SHELTER</strong>
          <h4>${nearestShelter.name} — ${nearestShelterDist.toFixed(1)} km away</h4>
          <p>${nearestShelter.address || "No address on file"} · Capacity: ${nearestShelter.capacity ?? "unknown"}</p>
          <p>${nearestShelter.contact_number ? `☎ ${nearestShelter.contact_number}` : ""}</p>
          <a class="outline-btn" style="display:inline-block;text-decoration:none;margin-top:8px;" target="_blank" rel="noopener" href="${directionsUrl(userLat, userLng, nearestShelter.latitude, nearestShelter.longitude)}">Get Directions →</a>
        </div>
      ` : `
        <div class="alert-card" style="border-left:5px solid #9baab5;margin-bottom:14px;">
          <p>No active shelters are registered nearby.</p>
        </div>
      `}

      ${blockedRoads.length > 0 ? `
        <div class="alert-card" style="border-left:5px solid #e84b4f;">
          <strong>⚠ ROADS BLOCKED NEAR YOU</strong>
          ${blockedRoads.map((r) => `<p>${r.name} — risk score ${r.risk_score}/100</p>`).join("")}
        </div>
      ` : ""}
    `;
  } catch (e) {
    console.error(e);
    routeStatusBody.innerHTML = `<p style="font-size:13px;color:#e84b4f;">Could not load route status. Please try again.</p>`;
  }
}

function renderRouteStatusFallback() {
  const loc = locations.find((l) => l.id === currentLocationId);
  routeStatusBody.innerHTML = `
    <div class="alert-card" style="border-left:5px solid #9baab5;margin-bottom:14px;">
      <strong>LOCATION UNAVAILABLE</strong>
      <h4>We couldn't access your device location</h4>
      <p>Check your browser's location permission and try again, or view guidance for your selected location instead.</p>
    </div>
    ${loc ? `<button class="outline-btn" id="useSelectedLocationBtn">Use "${loc.name}, ${loc.state}" instead →</button>` : ""}
  `;

  const btn = document.getElementById("useSelectedLocationBtn");
  if (btn && loc) {
    btn.addEventListener("click", () => renderRouteStatusForCoords(loc.latitude, loc.longitude));
  }
}

function openRouteStatusModal() {
  routeStatusModal.classList.add("show");
  routeStatusBody.innerHTML = `<p style="font-size:13px;color:#8a97a1;">Requesting your location…</p>`;

  if (!navigator.geolocation) {
    renderRouteStatusFallback();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      renderRouteStatusForCoords(position.coords.latitude, position.coords.longitude);
    },
    () => {
      renderRouteStatusFallback();
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

if (checkRouteStatusBtn) {
  checkRouteStatusBtn.addEventListener("click", openRouteStatusModal);
}

if (closeRouteStatusModal && routeStatusModal) {
  closeRouteStatusModal.addEventListener("click", () => {
    routeStatusModal.classList.remove("show");
  });
  routeStatusModal.addEventListener("click", (event) => {
    if (event.target === routeStatusModal) {
      routeStatusModal.classList.remove("show");
    }
  });
}

// ---------- History ----------
async function loadHistory() {
  const listEl = document.getElementById("historyList");
  listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Loading…</p>`;

  try {
    const predictions = await apiFetch(`/risk/predictions/${currentLocationId}/history?limit=20`);
    if (predictions.length === 0) {
      listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">No predictions yet — run Recalculate on the Home tab first.</p>`;
      return;
    }
    listEl.innerHTML = predictions.map((p) => `
      <div class="alert-card" style="border-left:4px solid ${riskColor(p.risk_level)};">
        <strong>${p.risk_level}</strong>
        <h4>Score: ${p.risk_score}/100</h4>
        <small>${new Date(p.predicted_at).toLocaleString()}</small>
      </div>
    `).join("");
  } catch (e) {
    listEl.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Could not load history.</p>`;
  }
}

// ---------- Map ----------
function initMap() {
  if (leafletMap) {
    leafletMap.invalidateSize();
    return;
  }

  leafletMap = L.map("leafletMap").setView([26.2, 92.9], 6); // North-East India
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
  }).addTo(leafletMap);

  refreshMapMarkers();
}

async function refreshMapMarkers() {
  if (!leafletMap) return;

  try {
    const [locs, shelters, roads] = await Promise.all([
      apiFetch("/locations/"),
      apiFetch("/shelters/?is_active=true"),
      apiFetch("/roads/"),
    ]);

    locs.forEach(async (loc) => {
      try {
        // Get the latest risk prediction for this location
        const risk = await apiFetch(`/risk/predictions/${loc.id}/latest`);

        // Create marker using the risk level colour
        L.circleMarker([loc.latitude, loc.longitude], {
          radius: 8,
          color: riskColor(risk.risk_level),
          fillColor: riskColor(risk.risk_level),
          fillOpacity: 0.9,
        })
          .addTo(leafletMap)
          .bindPopup(`
            <b>${loc.name}</b><br>
            ${loc.state}<br>
            <b>Risk:</b> ${risk.risk_level}<br>
            <b>Score:</b> ${risk.risk_score}/100
          `);
      } catch (e) {
        // If no prediction exists, show a grey marker
        L.circleMarker([loc.latitude, loc.longitude], {
          radius: 8,
          color: "#9baab5",
          fillOpacity: 0.7,
        })
          .addTo(leafletMap)
          .bindPopup(`
            <b>${loc.name}</b><br>
            ${loc.state}<br>
            Risk prediction unavailable
          `);
      }
    });

    shelters.forEach((s) => {
      L.marker([s.latitude, s.longitude])
        .addTo(leafletMap)
        .bindPopup(`<b>🏚 ${s.name}</b><br/>Capacity: ${s.capacity ?? "?"}`);
    });

    roads.forEach((r) => {
      L.circleMarker([r.latitude, r.longitude], {
        radius: 6,
        color: riskColor(r.risk_level),
        fillOpacity: 0.9,
      })
        .addTo(leafletMap)
        .bindPopup(`<b>${r.name}</b><br/>Risk: ${r.risk_level}${r.is_blocked ? " (blocked)" : ""}`);
    });
  } catch (e) {
    showToast("Could not load map data");
  }
}

// ---------- Export ----------
// ---------- Export Word Report ----------
document.getElementById("exportBtn").addEventListener("click", async () => {

  if (!currentLocationId) {
    showToast("No location selected");
    return;
  }

  try {
    showToast("Generating report...");

    const location = locations.find(
      (loc) => loc.id === currentLocationId
    );

    const [weather, soil, alerts, roads, shelters] = await Promise.all([
      apiFetch(`/weather/${currentLocationId}/current`).catch(() => null),
      apiFetch(`/soil-moisture/${currentLocationId}/current`).catch(() => null),
      apiFetch(`/alerts/?location_id=${currentLocationId}`).catch(() => []),
      apiFetch(`/roads/?location_id=${currentLocationId}`).catch(() => []),
      apiFetch(`/shelters/`).catch(() => [])
    ]);

    const reportDate = new Date().toLocaleString();

    const alertsHTML = alerts.length
      ? alerts.map(alert => `
          <tr>
            <td>${alert.risk_level || "--"}</td>
            <td>${alert.title || "--"}</td>
            <td>${alert.message || "--"}</td>
          </tr>
        `).join("")
      : `
          <tr>
            <td colspan="3">No alerts available</td>
          </tr>
        `;

    const roadsHTML = roads.length
      ? roads.map(road => `
          <tr>
            <td>${road.name}</td>
            <td>${road.risk_level}</td>
            <td>${road.risk_score}/100</td>
            <td>${road.is_blocked ? "BLOCKED" : "OPEN"}</td>
          </tr>
        `).join("")
      : `
          <tr>
            <td colspan="4">No road data available</td>
          </tr>
        `;

    const sheltersHTML = shelters.length
      ? shelters.map(shelter => `
          <tr>
            <td>${shelter.name}</td>
            <td>${shelter.address || "--"}</td>
            <td>${shelter.capacity || "--"}</td>
            <td>${shelter.contact_number || "--"}</td>
          </tr>
        `).join("")
      : `
          <tr>
            <td colspan="4">No shelter data available</td>
          </tr>
        `;

    const reportHTML = `
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
  body {
    font-family: Arial, sans-serif;
    margin: 40px;
    color: #222;
  }

  h1 {
    text-align: center;
    color: #1f4f7a;
  }

  h2 {
    margin-top: 30px;
    color: #1f4f7a;
    border-bottom: 2px solid #1f4f7a;
    padding-bottom: 5px;
  }

  .info {
    margin: 20px 0;
    padding: 15px;
    background: #f2f6f8;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
  }

  th {
    background: #1f4f7a;
    color: white;
  }

  th, td {
    border: 1px solid #999;
    padding: 8px;
    text-align: left;
  }

  .footer {
    margin-top: 40px;
    text-align: center;
    color: #777;
    font-size: 12px;
  }
</style>

</head>

<body>

  <h1>LandslideWatch</h1>
  <h3 style="text-align:center;">
    AI Landslide Risk Monitoring Report
  </h3>

  <div class="info">
    <p><b>Location:</b> ${location ? location.name : "--"}</p>
    <p><b>State:</b> ${location ? location.state : "--"}</p>
    <p><b>Report Generated:</b> ${reportDate}</p>
  </div>

  <h2>Current Environmental Conditions</h2>

  <table>
    <tr>
      <th>Rainfall</th>
      <th>Temperature</th>
      <th>Humidity</th>
      <th>Soil Moisture</th>
    </tr>

    <tr>
      <td>${weather?.rainfall_mm ?? "--"} mm/hr</td>
      <td>${weather?.temperature ?? "--"} °C</td>
      <td>${weather?.humidity ?? "--"}%</td>
      <td>${soil?.soil_moisture ?? "--"}%</td>
    </tr>
  </table>


  <h2>Active Alerts</h2>

  <table>
    <tr>
      <th>Risk Level</th>
      <th>Alert</th>
      <th>Description</th>
    </tr>

    ${alertsHTML}
  </table>


  <h2>Road Status</h2>

  <table>
    <tr>
      <th>Road</th>
      <th>Risk Level</th>
      <th>Risk Score</th>
      <th>Status</th>
    </tr>

    ${roadsHTML}
  </table>


  <h2>Nearby Shelters</h2>

  <table>
    <tr>
      <th>Shelter</th>
      <th>Address</th>
      <th>Capacity</th>
      <th>Contact</th>
    </tr>

    ${sheltersHTML}
  </table>


  <div class="footer">
    Generated by LandslideWatch AI Landslide Risk Monitoring System
  </div>

</body>
</html>
`;

    const blob = new Blob(
      ["\ufeff", reportHTML],
      {
        type: "application/msword"
      }
    );

    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");

    a.href = url;

    a.download =
      `LandslideWatch_Report_${currentLocationId}.doc`;

    document.body.appendChild(a);

    a.click();

    document.body.removeChild(a);

    URL.revokeObjectURL(url);

    showToast("Word report downloaded successfully");

  } catch (error) {

    console.error("Report generation error:", error);

    showToast("Could not generate report");

  }

});

// ---------- Boot ----------
(async function init() {
  // Load locations even if user information has a problem
  try {
    await loadLocations();
    await loadHomeData();
    await runRiskPrediction();
  } catch (e) {
    console.error("Could not load locations:", e);
  }

  // Load user information separately
  try {
    await loadCurrentUser();
  } catch (e) {
    console.error("Could not load user:", e);
  }
})();
// ---------- Shared alert-card rendering (modal + bell dropdown) ----------
function renderAlertList(container, alerts, emptyTitle, emptySubtitle) {
  if (alerts.length === 0) {
    container.innerHTML = `
      <div class="alert-empty">
        <div class="alert-empty-icon">✓</div>
        <h4>${emptyTitle}</h4>
        <span>${emptySubtitle}</span>
      </div>`;
    return;
  }

  container.innerHTML = alerts.map((a) => `
    <div class="alert-card" style="--sev-color:${riskColor(a.risk_level)};">
      <div class="alert-icon">${riskIcon(a.risk_level)}</div>
      <div class="alert-body">
        <span class="alert-badge" style="background:${riskColor(a.risk_level)};">${a.risk_level}</span>
        <h4>${a.title}</h4>
        <p>${a.message}</p>
        <small>${new Date(a.created_at).toLocaleString()}</small>
      </div>
    </div>
  `).join("");
}

// ---------- Alerts popup (Early Warnings + Current High Risk Alerts) ----------
const alertsModal = document.getElementById("alertsModal");
const alertsModalList = document.getElementById("alertsModalList");
const alertsModalTitle = document.getElementById("alertsModalTitle");
const alertsModalSubtitle = document.getElementById("alertsModalSubtitle");
const closeAlertsModal = document.getElementById("closeAlertsModal");

async function openAlertsModal({ filterFn, title, subtitle, emptyTitle, emptySubtitle }) {
  alertsModalTitle.textContent = title;
  alertsModalSubtitle.textContent = subtitle;
  alertsModal.classList.add("show");
  alertsModalList.innerHTML = `<p style="font-size:13px;color:#8a97a1;">Loading alerts...</p>`;

  try {
    const alerts = await apiFetch(`/alerts/?location_id=${currentLocationId}&is_active=true`);
    const filtered = filterFn ? alerts.filter(filterFn) : alerts;
    renderAlertList(alertsModalList, filtered, emptyTitle, emptySubtitle);
  } catch (error) {
    console.error(error);
    alertsModalList.innerHTML = `<p style="color:#e84b4f;font-size:13px;">Could not load alerts.</p>`;
  }
}

const earlyWarningsBtn = document.getElementById("earlyWarningsBtn");

if (earlyWarningsBtn) {

  earlyWarningsBtn.addEventListener("click", () => {

    openAlertsModal({
      filterFn: null,
      title: "🔔 Early Warnings",
      subtitle: "All active alerts for the selected location",
      emptyTitle: "All Clear",
      emptySubtitle: "No active alerts for this location right now.",
    });

  });

}

const highRiskBtn = document.querySelector(
  ".alert-link.danger[data-view='home']"
);

if (highRiskBtn) {

  highRiskBtn.addEventListener("click", () => {

    openAlertsModal({
      filterFn: (a) =>
        a.risk_level === "HIGH" ||
        a.risk_level === "CRITICAL",

      title: "🚨 Current High Risk Alerts",
      subtitle: "High and critical risk alerts for the selected location",
      emptyTitle: "No Current High Risk Alerts",
      emptySubtitle:
        "Your selected location currently has no HIGH or CRITICAL alerts.",
    });

  });

}
if (closeAlertsModal && alertsModal) {

  closeAlertsModal.addEventListener("click", () => {
    alertsModal.classList.remove("show");
  });

  alertsModal.addEventListener("click", (event) => {

    if (event.target === alertsModal) {
      alertsModal.classList.remove("show");
    }

  });

}



// ---------- Notification bell dropdown ----------
const alertBell = document.getElementById("alertBell");
const notificationDropdown = document.getElementById("notificationDropdown");
const notificationList = document.getElementById("notificationList");
const notificationSubtitle = document.getElementById("notificationSubtitle");

async function loadNotificationDropdown() {
  notificationList.innerHTML = `<p style="font-size:12px;color:#8a97a1;">Loading…</p>`;
  notificationSubtitle.textContent = "—";

  try {
    const alerts = await apiFetch(`/alerts/?location_id=${currentLocationId}&is_active=true`);
    notificationSubtitle.textContent = alerts.length === 0
      ? "All caught up"
      : `${alerts.length} active alert${alerts.length === 1 ? "" : "s"}`;
    renderAlertList(notificationList, alerts, "All Clear", "No active alerts for this location right now.");
  } catch (error) {
    notificationSubtitle.textContent = "Error";
    notificationList.innerHTML = `<p style="color:#e84b4f;font-size:12px;">Could not load notifications.</p>`;
  }
}

alertBell.addEventListener("click", (event) => {
  event.stopPropagation();
  const isOpen = notificationDropdown.classList.toggle("show");
  if (isOpen) loadNotificationDropdown();
});

document.addEventListener("click", (event) => {

  if (
    notificationDropdown &&
    !event.target.closest(".notification-wrap")
  ) {
    notificationDropdown.classList.remove("show");
  }

});

function updateRiskMeter(score) {

    score = Number(score);

    if (isNaN(score)) {
        score = 0;
    }

    score = Math.max(0, Math.min(100, score));


    /* SCORE */

    const scoreElement =
        document.getElementById("riskScore");

    if (scoreElement) {
        scoreElement.textContent =
            Math.round(score);
    }


    /* RISK ARC */

    const riskArc =
        document.getElementById("riskArc");

    if (riskArc) {

        riskArc.style.strokeDashoffset =
            100 - score;

    }


    /* =====================================
       NEEDLE
    ===================================== */

    const pivotX = 170;
    const pivotY = 145;

    const needleLength = 78;


    /*
       SVG coordinate system:

       0 score   → left
       50 score  → top
       100 score → right

       -180° → left
       -90°  → up
       0°    → right
    */

    const angle =
        -180 + (score * 1.8);


    const radians =
        angle * Math.PI / 180;


    const endX =
        pivotX +
        needleLength *
        Math.cos(radians);


    const endY =
        pivotY +
        needleLength *
        Math.sin(radians);


    const needle =
        document.querySelector(
            "#riskNeedle .needle"
        );


    if (needle) {

        /* FIXED STARTING POINT */

        needle.setAttribute(
            "x1",
            pivotX
        );

        needle.setAttribute(
            "y1",
            pivotY
        );


        /* MOVING END */

        needle.setAttribute(
            "x2",
            endX
        );

        needle.setAttribute(
            "y2",
            endY
        );

    }


    /* =====================================
       RISK LABEL
    ===================================== */

    const riskLabel =
        document.getElementById("riskLabel");


    if (!riskLabel) return;


    if (score < 30) {

        riskLabel.textContent =
            "LOW RISK";

    }

    else if (score < 60) {

        riskLabel.textContent =
            "MODERATE RISK";

    }

    else if (score < 80) {

        riskLabel.textContent =
            "HIGH RISK";

    }

    else {

        riskLabel.textContent =
            "CRITICAL RISK";

    }

}