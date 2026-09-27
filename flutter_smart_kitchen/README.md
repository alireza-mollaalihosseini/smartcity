# Smart Kitchen – Flutter app

Mobile client for the [smart kitchen backend](../smart_kitchen). It talks to the Flask REST API through
the Nginx proxy (`/api/*`).

## Features

* **Login:** Firebase Authentication (email/password) plus a JWT from the backend (`POST /api/login`),
  managed by a `Provider`-based `AuthProvider`.
* **Devices and live data:** device list (`/api/devices`) and live line charts per appliance
  (`/api/live-data/<device>`, drawn with `fl_chart`).
* **Predictions and alerts:** forecast view (`/api/predictions`) and alert history (`/api/alerts`).
* **Push notifications:** Firebase Cloud Messaging handlers for foreground, background and tapped
  notifications. The device token is sent to `/api/register-push-token`, but the backend does not
  implement that endpoint yet.
* **Offline cache:** last responses are kept with `shared_preferences`.

## Structure

```
lib/
├── main.dart                 # app entry, Firebase init, routes
├── models/sensor_data.dart
├── screens/                  # login, home, device detail, predictor, alerts
├── services/
│   ├── api_service.dart      # REST client (set baseUrl here)
│   ├── firebase_service.dart # auth + messaging
│   └── local_cache.dart
└── widgets/sensor_chart.dart
test/                         # widget test with a mock auth provider
```

## Setup

1. Point `ApiService.baseUrl` in `lib/services/api_service.dart` to your backend (the Nginx host).
2. Connect your own Firebase project (`flutterfire configure`). This replaces
   `android/app/google-services.json`, the iOS `GoogleService-Info.plist` and the Firebase options in
   `lib/main.dart`.
3. Run the app:

   ```bash
   flutter pub get
   flutter run
   ```
