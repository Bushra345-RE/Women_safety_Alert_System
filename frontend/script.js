const API = "http://127.0.0.1:5000/api";

function saveUser(u) {
  localStorage.setItem("shield_user", JSON.stringify(u));
}
function getUser() {
  try {
    return JSON.parse(localStorage.getItem("shield_user"));
  } catch {
    return null;
  }
}
function clearUser() {
  localStorage.removeItem("shield_user");
}

function requireAuth() {
  if (!getUser()) {
    window.location.href = "login.html";
    return false;
  }
  return true;
}
function requireGuest() {
  if (getUser()) {
    window.location.href = "dashboard.html";
  }
}

async function apiPost(path, body) {
  const r = await fetch(API + path, {
    method: "POST",
    mode: "cors",
    credentials: "include",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "Request failed");
  return j;
}

async function apiGet(path) {
  const r = await fetch(API + path, {
    method: "GET",
    mode: "cors",
    credentials: "include",
    headers: { Accept: "application/json" },
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "Request failed");
  return j;
}

async function apiPut(path, body) {
  const r = await fetch(API + path, {
    method: "PUT",
    mode: "cors",
    credentials: "include",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || "Request failed");
  return j;
}

function toast(msg, type = "success", duration = 4000) {
  const icons = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
  let wrap = document.getElementById("toastWrap");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.id = "toastWrap";
    wrap.className = "toast-wrap";
    document.body.appendChild(wrap);
  }
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.innerHTML = `<span style="font-size:16px">${icons[type] || "ℹ️"}</span>
                 <span style="color:var(--text-soft)">${msg}</span>`;
  wrap.appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transform = "translateX(40px)";
    t.style.transition = "0.3s";
    setTimeout(() => t.remove(), 310);
  }, duration);
}

function fv(id) {
  const e = document.getElementById(id);
  return e ? e.value.trim() : "";
}

function getGPS(ok, fail) {
  if (!navigator.geolocation) {
    toast("Geolocation not supported", "error");
    if (fail) fail();
    return;
  }
  navigator.geolocation.getCurrentPosition(ok, fail || (() => {}), {
    enableHighAccuracy: true,
    timeout: 12000,
  });
}

async function reverseGeo(lat, lng) {
  try {
    const r = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`,
    );
    const d = await r.json();
    return d.display_name || "";
  } catch {
    return "";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const tog = document.getElementById("navToggle");
  const links = document.getElementById("navLinks");
  if (tog && links)
    tog.addEventListener("click", () => links.classList.toggle("open"));
  const cur = window.location.pathname.split("/").pop();
  document.querySelectorAll(".nav-link").forEach((a) => {
    if (a.getAttribute("href") === cur) a.classList.add("active");
  });
});

// ── NO COUNTDOWN — removed completely ──

function playSiren(times = 6) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    for (let i = 0; i < times; i++) {
      const osc = ctx.createOscillator(),
        gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(660, ctx.currentTime + i * 0.45);
      osc.frequency.linearRampToValueAtTime(
        880,
        ctx.currentTime + i * 0.45 + 0.22,
      );
      gain.gain.setValueAtTime(0.28, ctx.currentTime + i * 0.45);
      gain.gain.exponentialRampToValueAtTime(
        0.001,
        ctx.currentTime + i * 0.45 + 0.4,
      );
      osc.start(ctx.currentTime + i * 0.45);
      osc.stop(ctx.currentTime + i * 0.45 + 0.42);
    }
  } catch {}
}

function sirenFlash(ms = 3000) {
  const el = document.getElementById("sirenFlash");
  if (!el) return;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), ms);
}

let _map = null;
function initMap(lat, lng) {
  const el = document.getElementById("map");
  if (!el) return;
  if (typeof L === "undefined") {
    el.innerHTML =
      '<div style="height:100%;display:flex;align-items:center;justify-content:center;color:var(--text-muted);font-style:italic;">📡 Map requires internet</div>';
    return;
  }
  if (_map) {
    _map.remove();
    _map = null;
  }
  _map = L.map("map").setView([lat, lng], 15);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "© CartoDB",
    subdomains: "abcd",
    maxZoom: 19,
  }).addTo(_map);
  const icon = L.divIcon({
    className: "",
    html: `<div style="width:18px;height:18px;border-radius:50%;background:#dc2626;border:3px solid #fff;box-shadow:0 0 18px rgba(220,38,38,0.9);"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
  });
  L.marker([lat, lng], { icon })
    .addTo(_map)
    .bindPopup("<b>📍 Your Location</b>")
    .openPopup();
}

function alertCard(a) {
  const url = `https://www.google.com/maps?q=${a.latitude},${a.longitude}`;
  return `
    <div class="alert-item anim-up">
      <div class="alert-pulse"></div>
      <div class="alert-body">
        <div class="alert-time">🕐 ${a.time}</div>
        <div class="alert-place">${a.address || "Location captured"}</div>
        <div class="alert-coords">${Number(a.latitude).toFixed(5)}, ${Number(a.longitude).toFixed(5)}</div>
      </div>
      <a href="${url}" target="_blank" class="alert-map-btn">🗺 View</a>
    </div>`;
}
