# GEDYON — Install on your iPhone (native app with live Apple Health)

The web app can't read Apple Health. The native app can — silently, every
time it opens, no export files ever again. This guide takes the repo to a
running app on your phone.

**What you need**
- A Mac with Xcode 15+ (free, from the Mac App Store) — *no Mac? see Path B*
- An Apple Developer account — free tier works for installing on YOUR phone
  (app re-signs weekly); the $99/yr account removes that and unlocks TestFlight
- Your iPhone + cable (or same WiFi)

---

## Path A — you have a Mac (about 30 minutes, first time)

1. **Get the code**
   ```bash
   git clone https://github.com/eligedyon/gedyon.git
   cd gedyon
   npm install
   ```

2. **Create the iOS project** (one time)
   ```bash
   npm run ios:init
   ```
   This copies `index.html` into `www/` and generates the `ios/` Xcode project.

3. **Open it in Xcode**
   ```bash
   npm run ios:open
   ```

4. **Signing** — in Xcode, click the blue **App** project icon → *Signing &
   Capabilities* tab:
   - Team: pick your Apple ID (add it via Xcode → Settings → Accounts if empty)
   - Bundle Identifier: keep `com.gedyon.trials` (or change if taken)

5. **Add HealthKit** — same *Signing & Capabilities* tab:
   - **+ Capability** → search **HealthKit** → add it
   - (Leave "Clinical Health Records" off)

6. **Usage descriptions** — open `ios/App/App/Info.plist` and add inside the
   top-level `<dict>`:
   ```xml
   <key>NSHealthShareUsageDescription</key>
   <string>GEDYON reads your workouts, heart rate, HRV, sleep and VO2max to place you correctly in your Olympic Trials training plan.</string>
   <key>NSHealthUpdateUsageDescription</key>
   <string>GEDYON does not write health data.</string>
   ```

7. **Run it** — plug in your iPhone, pick it in the device dropdown (top bar),
   press ▶. First run: on the phone, Settings → General → VPN & Device
   Management → trust your developer certificate. The app opens, and the
   Connect tab's Apple Health card now does a REAL live connection —
   `connectAppleHealth()` finds the HealthKit bridge and asks permission once.

8. **Updating later** — after any change to `index.html`:
   ```bash
   git pull && npm run ios:sync
   ```
   then press ▶ in Xcode again.

## Path B — no Mac: Codemagic cloud build

[Codemagic](https://codemagic.io) builds iOS apps on rented Macs. Free tier
is enough for personal builds. You still need the **$99/yr Apple Developer
account** (free Apple IDs can't sign apps off-Mac), and distribution happens
through **TestFlight** (Apple's install-from-a-link system).

1. Sign up at codemagic.io with your GitHub account, add the `gedyon` repo
2. In the Apple Developer portal, create an App ID `com.gedyon.trials` with
   the HealthKit capability, and an App Store Connect app entry
3. In Codemagic: add your App Store Connect API key (Teams → integrations)
4. Add a `codemagic.yaml` (ask Claude to generate one when you get here —
   it needs your team ID) that runs: `npm install && npm run sync:web &&
   npx cap add ios`, injects the Info.plist keys from step 6 above, builds,
   and publishes to TestFlight
5. Install **TestFlight** on your iPhone → open the invite link → install
   GEDYON like a real app

## What changes once it's installed

- The Apple Health card stops talking about export files — it becomes a
  one-tap live connection (the code path already exists: `syncHealthData()`
  runs on every open and reads HRV, resting HR, sleep, VO2max and workouts
  since the last sync)
- Opening the app IS the sync. Fitness placement always uses current data
- The web app at eligedyon.github.io/gedyon keeps working unchanged — same
  data, synced through Supabase when signed in

## Gotchas

- **Free Apple ID**: app expires after 7 days — just press ▶ in Xcode again
  to re-install. The $99 account removes this.
- **HealthKit needs a real iPhone** — the Xcode Simulator has no health data
- If the device dropdown doesn't show your phone: unlock it, tap "Trust This
  Computer", and enable Developer Mode (Settings → Privacy & Security)
