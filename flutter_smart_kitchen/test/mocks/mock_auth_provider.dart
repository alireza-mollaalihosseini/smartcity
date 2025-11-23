// test/mocks/mock_auth_provider.dart
import 'package:flutter/material.dart';

class MockAuthProvider extends ChangeNotifier {
  bool _isSignedIn = false;
  String? _tenantId = 'test-tenant';  // Mock tenant for home screen if needed

  bool get isSignedIn => _isSignedIn;
  String? get tenantId => _tenantId;
  String? get jwtToken => 'mock-jwt';  // For predictor if navigated

  Future<bool> signIn({
    required String email,
    required String password,
    required BuildContext context,
  }) async {
    await Future.delayed(const Duration(milliseconds: 500));  // Simulate async
    _isSignedIn = true;
    notifyListeners();
    return true;
  }

  Future<void> signOut() async {
    _isSignedIn = false;
    notifyListeners();
  }
}