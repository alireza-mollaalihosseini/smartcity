// services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // CHANGE THIS TO YOUR PUBLIC EC2 / NGINX URL
  static const String baseUrl = 'http://localhost:8080'; // e.g. http://54.123.45.67:8080

  static Future<Map<String, dynamic>?> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/login'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'email': email, 'password': password}),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      }
    } catch (e) {
      print('Login API error: $e');
    }
    return null;
  }

  static Future<void> registerPushToken({
    required String jwtToken,
    required String tenantId,
    required String fcmToken,
  }) async {
    try {
      await http.post(
        Uri.parse('$baseUrl/api/register-push-token'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $jwtToken',
        },
        body: json.encode({
          'tenant_id': tenantId,
          'fcm_token': fcmToken,
        }),
      );
    } catch (e) {
      print('Failed to register FCM token: $e');
    }
  }

  static Future<List<dynamic>> getDevices(String token) async {
    return _getList('$baseUrl/api/devices', token);
  }

  static Future<List<Map<String, dynamic>>> getLiveData(String token, String device) async {
    final data = await _getList('$baseUrl/api/live-data/$device', token);
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> getPredictions(String token) async {
    final data = await _getList('$baseUrl/api/predictions', token);
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> getAlerts(String token) async {
    final data = await _getList('$baseUrl/api/alerts', token);
    return data.cast<Map<String, dynamic>>();
  }

  // Helper
  static Future<List<dynamic>> _getList(String url, String token) async {
    try {
      final response = await http.get(
        Uri.parse(url),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      }
    } catch (e) {
      print('API Error ($url): $e');
    }
    return [];
  }
}