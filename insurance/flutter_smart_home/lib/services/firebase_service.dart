// services/firebase_service.dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'api_service.dart';
// Removed: import 'package:flutter/foundation.dart';

class AuthProvider with ChangeNotifier {
  User? _user;
  String? _jwtToken;
  String? _tenantId;
  String? _fcmToken;

  User? get user => _user;
  String? get jwtToken => _jwtToken;
  String? get tenantId => _tenantId;
  String? get fcmToken => _fcmToken;
  bool get isSignedIn => _user != null && _jwtToken != null;

  final FirebaseAuth _auth = FirebaseAuth.instance;
  final FirebaseMessaging _messaging = FirebaseMessaging.instance;

  BuildContext? _tempContext;

  AuthProvider() {
    _setupFirebaseMessaging();
  }

  void _setupFirebaseMessaging() {
    _requestPermission();
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
    FirebaseMessaging.onBackgroundMessage(_backgroundHandler);
  }

  Future<void> _requestPermission() async {
    final settings = await _messaging.requestPermission(
      alert: true, badge: true, sound: true, provisional: false,
    );
    if (settings.authorizationStatus == AuthorizationStatus.authorized) {
      debugPrint('🔔 Notifications authorized');
    }
  }

  Future<void> _registerFcmToken() async {
    final token = await _messaging.getToken();
    if (token != null && _jwtToken != null && _tenantId != null) {
      _fcmToken = token;
      await ApiService.registerPushToken(
        jwtToken: _jwtToken!,
        tenantId: _tenantId!,
        fcmToken: token,
      );
      debugPrint('✅ FCM Token sent to backend');
    }
  }

  void _handleForegroundMessage(RemoteMessage message) {
    if (message.notification != null && _tempContext != null) {
      ScaffoldMessenger.of(_tempContext!).showSnackBar(
        SnackBar(
          content: Text(message.notification!.title ?? "Smart Home Insurance Alert"),
          backgroundColor: Colors.blue[700],
          duration: const Duration(seconds: 6),
          action: SnackBarAction(
            label: 'VIEW',
            textColor: Colors.white,
            onPressed: () => _navigateFromNotification(message),
          ),
        ),
      );
    }
  }

  void _handleNotificationTap(RemoteMessage message) {
    if (_tempContext != null) {
      _navigateFromNotification(message);
    }
  }

  void _navigateFromNotification(RemoteMessage message) {
    final screen = message.data['screen'] ?? message.data['route'];
    final nav = Navigator.of(_tempContext!);

    if (screen == 'alerts') {
      nav.pushNamed('/alerts');
    } else if (screen == 'predictions') {
      nav.pushNamed('/predictions');
    } else {
      nav.pushNamed('/home');
    }
  }

  // ===================== AUTH =====================
  Future<bool> signIn({
    required String email,
    required String password,
    required BuildContext context,
  }) async {
    _tempContext = context;

    try {
      await _auth.signInWithEmailAndPassword(email: email, password: password);
      _user = _auth.currentUser;

      final jwtData = await ApiService.login(email, password);
      if (jwtData != null) {
        _jwtToken = jwtData['token'];
        _tenantId = jwtData['tenant_id'];
        notifyListeners();

        await _registerFcmToken();  // ← Critical: register device for alerts
        return true;
      }
    } catch (e) {
      debugPrint('Sign in failed: $e');
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Login failed: ${e.toString()}')),
        );
      }
    } finally {
      _tempContext = null;
    }
    return false;
  }

  Future<void> signOut() async {
    await _auth.signOut();
    await _messaging.deleteToken();
    _user = null;
    _jwtToken = null;
    _tenantId = null;
    _fcmToken = null;
    notifyListeners();
  }
}

// Required top-level function for background messages
@pragma('vm:entry-point')
Future<void> _backgroundHandler(RemoteMessage message) async {
  debugPrint("🔔 Background notification: ${message.messageId}");
}