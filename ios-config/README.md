# iOS release config

The `ios/` Xcode project is generated on your Mac (`npm run ios:init`) and is not
committed. Before archiving for TestFlight / App Store:

1. Copy `PrivacyInfo.xcprivacy` into `ios/App/App/` and add it to the App target
   in Xcode (File → Add Files, tick "App"). Apple requires a privacy manifest.
2. Paste `Info.plist.additions.xml` into `ios/App/App/Info.plist`.
3. Signing & Capabilities → add **HealthKit** and **In-App Purchase**.
4. In `index.html`, set `REVENUECAT_IOS_KEY` to the public Apple key from
   RevenueCat (starts with `appl_`) and make sure the entitlement id matches
   `KODA_ENTITLEMENT` (`koda_unlimited`).
5. `npm install && npm run ios:sync`, then Product → Archive in Xcode.

The App Privacy answers in App Store Connect must match the manifest: Email,
Name, Health, Fitness, Photos, Other User Content, Purchase History and User ID,
all linked to the user, none used for tracking, purpose App Functionality.
