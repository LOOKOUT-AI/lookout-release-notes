# LOOKOUT — Breakout Sales Strategy

**Date:** 2026-06-20
**Author:** David (with strategy assist)
**Status:** Draft for discussion
**Objective:** Identify and sequence the initiative(s) most likely to produce a **step-change ("breakout") in sales**, not just incremental improvement.

---

## 0. Context: what we're building on

From the shipped product (v2.5 → v3.4.4), LOOKOUT today is a **marine AI situational-awareness camera platform**:

- **Streaming:** multi-camera live video to MFDs and arbitrary displays, 360 mode, PTZ, RTSP/FLIR support, split-screen, over-under view, low-bandwidth streaming.
- **Perception:** object-detection + multi-object-tracking neural nets, "tap to train," horizon detection, accurate detection placement.
- **AR / visualization:** 3D aerial view, AR overlays, IMU horizon stabilization, animated wake effects, 3D boat picker.
- **Marine data:** NMEA, AIS Class B with names, Argo/GPX routes, charts.
- **Modes:** coastal, night-mode UI, panorama, automatic recording.

**Key strategic asset:** we already own *streaming + detection + AR* on installed hardware. The options below are best judged by how much they **leverage that asset** versus how much net-new capability they require. The boat also sits **idle and unattended ~90%+ of its life** — a fact that strongly favors any option that creates value at the dock/at anchor, not just underway.

---

## 1. The five options, fleshed out

### Option A — "LOOKOUT Anywhere": remote viewing + Security Mode
**What:** A companion app (mobile + web) that lets owners tune into their boat's cameras from anywhere — including the 3D/aerial view — plus a **Security Mode** that uses our existing person-detection net to alert when someone boards the unattended vessel (push notification + clip).

**Why it's a breakout candidate:**
- **Opens a brand-new use case** on hardware we've already sold: at-dock / at-anchor monitoring and anti-theft, addressing the 90%+ of the time the boat is idle.
- **First recurring-revenue line** (cloud relay, alert/clip storage, multi-boat fleet view) — changes the business model from one-time hardware to ARR.
- **Killer demo:** "watch your boat from your phone, get alerted if someone steps aboard" sells itself at shows and in video.
- **High leverage:** reuses streaming, detection, 360, aerial — mostly integration + cloud + app, not new core CV.

**Risks / cost:** cloud infra (NAT traversal/relay, storage), connectivity dependence (marine cellular/Starlink is spotty), false-alarm tuning, security/privacy liability, app-store + notification ops, ongoing cost-to-serve. Rear/stern coverage strengthens it (see Option D dependency).

### Option B — Improve the night-vision system
**What:** Better low-light perception — sensor/ISP tuning, a low-light-tuned detector, possibly IR/thermal fusion (we already ingest FLIR via RTSP).

**Why it matters:** Night is when collisions/groundings are scariest and when our value peaks; strong **safety differentiator** vs. plain chartplotters; **hard to do well → defensible moat**; directly strengthens the defense story (Option E).

**Risks / cost:** may require hardware (sensor/IR illuminator) → couples to the housing program; long R&D; **hard to demo in a daylight boat-show hall**; deepens an existing capability rather than opening a new buyer.

### Option C — More convincing 3D aerial view (buoy lighting + wind particle FX)
**What:** Visual polish to the AR/aerial scene — animated buoy/nav lights, wind particle effects, richer rendering.

**Why it matters:** Demo "wow," marketing eye-candy, closes deals at shows and in video; **cheap and fast** (front-end/graphics); reinforces the premium/futuristic brand.

**Risks / cost:** it's eye-candy, not a job-to-be-done; adds no safety value and opens no new segment; easy to over-invest. **Best treated as a cheap marketing multiplier, not a standalone strategic bet.**

### Option D — New camera housing (bow + stern)
**What:** Industrial-design program for front and rear camera units → full coverage, cleaner install, weatherproofing, brand identity, dealer-shelf presence.

**Why it matters:** Front+rear coverage is a real gap and an **enabler** for docking/security (A) and possibly night sensors (B); better install = fewer support tickets; physical product = harder to copy, better margins, retail channel.

**Risks / cost:** hardware = tooling capex, certification, inventory, supply chain, **long lead times**; adds no software value on its own. Strategic value is largely as an *enabler* of A and B.

### Option E — CV distance estimation for defense + smart autopilots
**What:** Sharpen and certify monocular/stereo **range estimation**, packaged as a perception module licensed/sold to defense (USVs, force protection) and autopilot/autonomy partners (B2B / OEM).

**Why it matters:** **Largest TAM and highest contract values**; shifts revenue from consumer-hardware margins to software/licensing/contracts; leverages our core CV moat; the truest "breakout" in revenue *scale*. Reinforced by night vision (B).

**Risks / cost:** long procurement/sales cycles; compliance (ITAR/defense); different GTM motion + talent; accuracy/safety bar is very high; partner dependency; risk of distracting the consumer core. **High upside, high variance, slow to revenue.**

---

## 2. Decision-making matrix

### Criteria & weights (objective = breakout / near-term step-change in sales)

| Criterion | Weight | Rationale |
|---|---:|---|
| Revenue upside / new revenue (TAM, recurring) | 25% | Breakout = materially bigger or new revenue |
| Speed to revenue | 20% | "Breakout sales" implies near-term impact |
| Leverage of existing assets | 15% | Reuse → faster, cheaper, lower risk |
| Capital efficiency (low cost & risk) | 15% | Avoid capex/ongoing-cost traps |
| Moat / defensibility | 15% | Durable, not easily copied |
| Demo & sales-closing power | 10% | Helps win at shows / in video / pilots |

Scores are 1–5 (5 = best). For "capital efficiency," higher = cheaper/lower-risk.

### Scenario 1 — "Breakout sales" weighting (above)

| Option | Rev. upside (25) | Speed (20) | Leverage (15) | Capital eff. (15) | Moat (15) | Demo (10) | **Weighted** | Rank |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **A — Anywhere + Security** | 5 | 4 | 5 | 3 | 3 | 5 | **4.20** | **1** |
| C — Aerial realism FX | 2 | 5 | 5 | 5 | 1 | 4 | **3.55** | 2 |
| E — Defense / autopilot CV | 5 | 1 | 4 | 2 | 5 | 2 | **3.30** | 3 |
| B — Night vision | 3 | 2 | 3 | 2 | 5 | 2 | **2.85** | 4 |
| D — Housing (bow/stern) | 4 | 1 | 2 | 1 | 4 | 3 | **2.55** | 5 |

### Scenario 2 — "Durable franchise / long-horizon" weighting (sensitivity check)
Weights: Revenue 30, Moat 25, Leverage 15, Speed 10, Capital 10, Demo 10.

| Option | **Weighted** | Rank |
|---|:--:|:--:|
| **A — Anywhere + Security** | **4.20** | **1** |
| E — Defense / autopilot CV | 3.85 | 2 |
| B — Night vision | 3.20 | 3 |
| C — Aerial realism FX | 3.00 | 4 (tie) |
| D — Housing | 3.00 | 4 (tie) |

**Read-through from the sensitivity check:**
- **A is the robust #1 under both lenses** → it's the no-regret lead bet.
- **E is the most time-horizon-sensitive option** (#3 short-term, #2 long-term) → seed it now, harvest later; don't expect near-term sales from it.
- **C's value is *only* speed/cheapness** — it collapses under the long-horizon lens. Treat it as a tactical marketing multiplier, never a flagship.
- **B and D are foundational/enabling**, not breakout drivers on their own.

---

## 3. Dependencies (these options are not independent)

- **Security Mode (A)** is materially better with **stern coverage (D)** — but can launch on existing/forward cameras first.
- **Night vision (B)** may require a **sensor/IR change → housing (D)**; decide the hardware question before committing B's scope.
- **Defense/autopilot (E)** is fed by **night vision (B)** (range + low-light are core defense asks) and our core CV.
- **Aerial FX (C)** is pure marketing leverage — it makes **A's** "watch from your phone" demo and show-floor pitches land harder.

---

## 4. Recommendation & sequencing

**Lead bet:** Ship **Option A — "LOOKOUT Anywhere" + Security Mode** as the flagship breakout driver. It's the only option that scores #1 under both time horizons, opens a new use case on installed hardware, gives us our first recurring revenue, and is the strongest demo. Highest leverage of what we already own.

### Roadmap

**Now (Q3 2026) — the breakout wedge**
1. **Option A** as the flagship: remote viewing + Security Mode (person-aboard alerts, clip storage, multi-boat view). Reuse streaming + detection + aerial; stand up the cloud relay + subscription.
2. **Option C in parallel** (small graphics effort): buoy/nav-light + wind FX — *scoped as a marketing/demo multiplier* for A, not a standalone release.

**Next (Q4 2026 → H1 2027) — deepen the moat**
3. **Option B (night vision)** as a funded R&D track — it's the safety differentiator and the defense enabler. **Decide early** whether it needs a hardware/sensor change.
4. **Option D (housing)** scoped explicitly as the **enabler** of A's stern coverage and B's sensor needs — not a standalone bet. Start tooling once A validates demand and B's sensor decision is made.

**Parallel long-horizon (seed now, revenue 2027+)**
5. **Option E (defense / autopilot CV):** stand up a *small* effort — 2–3 design partners, distance-estimation accuracy benchmarks, pilots. Plant it now because it's the true revenue-*scale* breakout and it's fed by B — but firewall it so it doesn't consume the consumer roadmap.

### Decision guardrails
- **Kill/kept gate for C:** cap the FX effort; if it slips past a small fixed budget, ship A without it.
- **Gate D and B together** on the sensor decision — don't tool a housing twice.
- **Firewall E's GTM** (separate owner) so long defense sales cycles don't starve the consumer roadmap.
- **Re-run the matrix** if the objective shifts from "accelerate consumer sales" to "establish a defense franchise" — that flips weights toward E and B.

---

## 5. One-line summary

> **Lead with "LOOKOUT Anywhere + Security Mode" (A)** — it's the robust, high-leverage, recurring-revenue breakout. Use **aerial FX (C)** as a cheap parallel marketing multiplier, treat **night vision (B)** and **housing (D)** as the sequenced moat/enabler track, and **seed the defense/autopilot CV play (E)** now for a 2027+ revenue-scale breakout.
