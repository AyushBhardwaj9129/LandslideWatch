// ============================================================
// LandslideWatch Assistant
// A lightweight, rule-based chat widget (no external AI calls).
// It reuses the same globals/functions app.js already exposes
// (switchView, currentLocationId, locations, runRiskPrediction,
// openRouteStatusModal, logout, etc.) so every action it performs
// is identical to clicking the equivalent button in the UI.
// ============================================================

(function () {
  // ---- View navigation aliases ----
  const VIEW_ALIASES = {
    home: ["home", "dashboard", "overview", "main page"],
    map: ["map", "risk map"],
    forecast: ["forecast", "prediction", "predictions"],
    routes: ["routes", "roads", "road status"],
    shelters: ["shelter"],
    history: ["my history", "action history", "past actions", "history"],
    "alert-history": ["alert history", "past alerts", "alert log"],
    settings: ["settings", "account"],
    about: ["about", "how it works"],
  };
  const NAV_VERBS = ["go to", "navigate to", "open", "show me", "show", "view", "take me to", "switch to page"];

  // ---- Built-in safety / product FAQ knowledge base ----
  const FAQS = [
    {
      keywords: ["risk formula", "how is risk calculated", "how do you calculate risk", "risk score calculated"],
      answer: "Risk Score = (Rainfall × 0.40) + (Soil Erosion × 0.30) + (Humidity × 0.20) + (Temperature × 0.10), each factor normalized 0–100. Full breakdown is on the About page."
    },
    {
      keywords: ["risk level", "what does high risk mean", "what does critical mean", "what does moderate mean", "what is low risk"],
      answer: "Risk levels: 0–25 Low, 26–50 Moderate, 51–75 High, 76–100 Very High/Critical. The higher the score, the sooner you should act."
    },
    {
      keywords: ["what causes landslide", "why do landslides happen", "landslide causes"],
      answer: "Landslides here are mainly driven by heavy rainfall and soil erosion, with humidity and temperature acting as supporting factors that weaken slopes over time."
    },
    {
      keywords: ["evacuat", "what should i do", "in an emergency", "danger", "high risk alert"],
      answer: "If your area shows High or Critical risk: check Route Status for safe roads, locate your nearest shelter, and follow local authority evacuation orders immediately."
    },
    {
      keywords: ["soil moisture", "soil erosion"],
      answer: "Soil moisture/erosion reflects how saturated the ground is — wetter, looser soil is far more likely to give way during heavy rain."
    },
    {
      keywords: ["what is this app", "who made this", "landslidewatch"],
      answer: "LandslideWatch is an early-warning system that combines live rainfall, soil, humidity and temperature data into a landslide risk score for monitored locations across North-East India."
    },
    {
      keywords: ["export", "download report"],
      answer: "You can download a full data report (weather, risk, alerts, roads) for your selected location. Just ask me to \"export report\"."
    },
  ];

  const state = { locationPromptActive: false };
  const els = {};

  // Generic "show me what you can do" style follow-ups — words/phrases with
  // no concrete topic of their own, so the best response is the option menu.
  const GENERIC_HELP_WORDS = ["next", "more", "options", "option", "menu", "help", "commands", "what else"];
  const GENERIC_HELP_PHRASES = [
    "what can you do",
    "what can i ask",
    "what can i say",
    "show options",
    "show me options",
    "show me what you can do",
    "what are my options",
  ];
  const MENU_OPTIONS = [
    "Show shelters",
    "Check my risk",
    "Refresh forecast",
    "Check route status",
    "Show high risk alerts",
    "How is risk calculated?",
  ];

  function q(id) {
    return document.getElementById(id);
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function addMessage(html, sender) {
    const msg = document.createElement("div");
    msg.className = `assistant-msg ${sender}`;
    msg.innerHTML = html;
    els.messages.appendChild(msg);
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  function setQuickReplies(options) {
    els.quickReplies.innerHTML = "";
    (options || []).forEach((opt) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "assistant-chip";
      btn.textContent = opt;
      btn.addEventListener("click", () => handleUserText(opt));
      els.quickReplies.appendChild(btn);
    });
  }

  function findLocationMatch(lowerText) {
    if (typeof locations === "undefined" || !Array.isArray(locations)) return null;
    return (
      locations.find((loc) => lowerText.includes(`${loc.name}, ${loc.state}`.toLowerCase())) ||
      locations.find((loc) => lowerText.includes(loc.name.toLowerCase())) ||
      null
    );
  }

  function setLocation(loc) {
    const select = q("locationSelect");
    if (!select) return false;
    select.value = String(loc.id);
    select.dispatchEvent(new Event("change"));
    return true;
  }

  function matchView(lower) {
    for (const [view, aliases] of Object.entries(VIEW_ALIASES)) {
      if (aliases.some((a) => lower.includes(a))) return view;
    }
    return null;
  }

  function goTo(view) {
    if (typeof switchView === "function") {
      switchView(view);
      return true;
    }
    return false;
  }

  function respond(text) {
    const lower = text.toLowerCase().trim();

    // Follow-up: assistant previously asked "which location?"
    if (state.locationPromptActive) {
      state.locationPromptActive = false;
      const loc = findLocationMatch(lower);
      if (loc) {
        setLocation(loc);
        addMessage(`Switched to <b>${escapeHtml(loc.name)}, ${escapeHtml(loc.state)}</b>.`, "bot");
      } else {
        addMessage("I couldn't find that in the monitored locations list — try picking one from the dropdown at the top instead.", "bot");
      }
      return;
    }

    // ---- Generic "show me options" style follow-ups ----
    // A bare word like "next" or "help" has no topic of its own to act on,
    // so treat it as a request to see what the assistant can do.
    const isGenericHelp =
      GENERIC_HELP_WORDS.includes(lower) || GENERIC_HELP_PHRASES.some((p) => lower.includes(p));
    if (isGenericHelp) {
      addMessage("Here's what I can help with — tap one or type your own:", "bot");
      setQuickReplies(MENU_OPTIONS);
      return;
    }

    // ---- Navigation ----
    const view = matchView(lower);
    const looksLikeNavCommand = view && (NAV_VERBS.some((v) => lower.includes(v)) || lower.split(" ").length <= 3);
    if (looksLikeNavCommand) {
      const label = view.replace("-", " ");
      if (goTo(view)) {
        addMessage(`Opening <b>${escapeHtml(label)}</b>…`, "bot");
      } else {
        addMessage("Sorry, I couldn't navigate there right now.", "bot");
      }
      return;
    }

    // ---- Risk recalculation ----
    if (/(recalculate|refresh|update).*risk|check (my |the )?risk\b/.test(lower)) {
      goTo("home");
      addMessage("Recalculating risk for your selected location…", "bot");
      setTimeout(() => {
        if (typeof runRiskPrediction === "function") runRiskPrediction();
      }, 250);
      return;
    }

    // ---- Forecast refresh ----
    if (/(refresh|generate|update).*forecast/.test(lower)) {
      goTo("forecast");
      addMessage("Refreshing the forecast…", "bot");
      setTimeout(() => {
        const btn = q("generateForecastBtn");
        if (btn) btn.click();
      }, 250);
      return;
    }

    // ---- Route status ----
    if (/\broute\b|road.*safe|safe.*road|am i safe|check.*road|safest (way|road)|best (way|road)|which (way|road)|which route/.test(lower)) {
      if (typeof openRouteStatusModal === "function") {
        openRouteStatusModal();
        addMessage("Checking the safest route based on your current location…", "bot");
      } else {
        addMessage("Sorry, route status isn't available right now.", "bot");
      }
      return;
    }

    // ---- Export report ----
    if (/export|download.*report/.test(lower)) {
      const btn = q("exportBtn");
      if (btn) {
        btn.click();
        addMessage("Generating your data report…", "bot");
      } else {
        addMessage("Couldn't find the export action.", "bot");
      }
      return;
    }

    // ---- High risk alerts ----
    if (/high risk alert|critical alert/.test(lower)) {
      const btn = document.querySelector(".alert-link.danger[data-view='home']");
      if (btn) {
        btn.click();
        addMessage("Here are the current high risk alerts.", "bot");
      }
      return;
    }

    // ---- Early warnings ----
    if (/early warning/.test(lower)) {
      const btn = q("earlyWarningsBtn");
      if (btn) {
        btn.click();
        addMessage("Here are the early warnings.", "bot");
      }
      return;
    }

    // ---- Explicit location change (name not yet given) ----
    if (/(change|switch|set).*location|different location/.test(lower)) {
      const loc = findLocationMatch(lower);
      if (loc) {
        setLocation(loc);
        addMessage(`Switched to <b>${escapeHtml(loc.name)}, ${escapeHtml(loc.state)}</b>.`, "bot");
      } else {
        state.locationPromptActive = true;
        addMessage("Sure — which location? (e.g. Guwahati, Silchar, Cherrapunji)", "bot");
      }
      return;
    }

    // ---- Log out ----
    if (/log ?out|sign ?out/.test(lower)) {
      addMessage("Signing you out…", "bot");
      setTimeout(() => {
        if (typeof logout === "function") logout();
      }, 400);
      return;
    }

    // ---- FAQ knowledge base ----
    const faq = FAQS.find((f) => f.keywords.some((k) => lower.includes(k)));
    if (faq) {
      addMessage(faq.answer, "bot");
      return;
    }

    // ---- Implicit location switch (a location name was just mentioned) ----
    const implicitLoc = findLocationMatch(lower);
    if (implicitLoc) {
      setLocation(implicitLoc);
      addMessage(`Switched to <b>${escapeHtml(implicitLoc.name)}, ${escapeHtml(implicitLoc.state)}</b>.`, "bot");
      return;
    }

    // ---- Fallback ----
    addMessage(
      "I didn't quite get that. I can navigate the app (\"show shelters\", \"open forecast\") or answer quick questions (\"how is risk calculated?\").",
      "bot"
    );
    setQuickReplies(MENU_OPTIONS);
  }

  function handleUserText(raw) {
    const text = (raw || "").trim();
    if (!text) return;
    addMessage(escapeHtml(text), "user");
    els.input.value = "";
    setQuickReplies([]);
    setTimeout(() => respond(text), 200);
  }

  function openPanel() {
    els.panel.classList.add("show");
    els.toggle.classList.add("hide");
    els.input.focus();
  }

  function closePanel() {
    els.panel.classList.remove("show");
    els.toggle.classList.remove("hide");
  }

  function init() {
    els.widget = q("assistantWidget");
    if (!els.widget) return;

    els.toggle = q("assistantToggle");
    els.panel = q("assistantPanel");
    els.close = q("assistantClose");
    els.messages = q("assistantMessages");
    els.quickReplies = q("assistantQuickReplies");
    els.form = q("assistantForm");
    els.input = q("assistantInput");

    els.toggle.addEventListener("click", openPanel);
    els.close.addEventListener("click", closePanel);
    els.form.addEventListener("submit", (e) => {
      e.preventDefault();
      handleUserText(els.input.value);
    });

    addMessage("Hi! I'm your LandslideWatch assistant. I can jump to any page or answer quick safety questions.", "bot");
    setQuickReplies(MENU_OPTIONS);
  }

  document.addEventListener("DOMContentLoaded", init);
})();