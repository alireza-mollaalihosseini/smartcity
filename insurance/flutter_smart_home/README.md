# Smart Home – Flutter app (insurance demo)

Policyholder app for the [smart home backend](../smart_home). It shares its architecture with the
[smart kitchen app](../../flutter_smart_kitchen): Firebase Authentication plus a backend JWT for login,
the device list, live charts, predictions and the alert history, all served by the Flask API behind
Nginx (`/api/*`).

## Setup

1. Set `ApiService.baseUrl` in `lib/services/api_service.dart` to your backend host.
2. Connect your own Firebase project (`flutterfire configure`) and replace
   `android/app/google-services.json` and the Firebase options in `lib/main.dart`.
3. Run the app:

   ```bash
   flutter pub get
   flutter run
   ```
