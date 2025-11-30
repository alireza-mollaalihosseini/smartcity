// lib/services/local_cache.dart - Corrected version with proper string interpolation
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class LocalCache {
  static const String _alertsKey = 'alerts_cache';
  static const String _sensorKey = 'sensor_data_cache';
  static const int _maxEntries = 100;

  static Future<void> saveAlerts(List<Map<String, dynamic>> alerts) async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getStringList(_alertsKey) ?? [];
    cached.clear(); // Overwrite for alerts to keep latest
    cached.addAll(alerts.take(_maxEntries).map((alert) => json.encode({
      ...alert,
      'cached_at': DateTime.now().toIso8601String(),
    })));
    await prefs.setStringList(_alertsKey, cached);
  }

  static Future<List<Map<String, dynamic>>> getCachedAlerts() async {
    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getStringList(_alertsKey) ?? [];
    return cached.map((e) => json.decode(e) as Map<String, dynamic>).toList();
  }

  static Future<void> saveSensorData(String device, Map<String, dynamic> data) async {
    final prefs = await SharedPreferences.getInstance();
    final key = '${_sensorKey}_$device';  // Fixed: Use '${_sensorKey}_$device' to avoid interpolation issues
    final cached = prefs.getStringList(key) ?? [];
    cached.add(json.encode({
      ...data,
      'cached_at': DateTime.now().toIso8601String(),
    }));
    if (cached.length > _maxEntries) cached.removeAt(0);
    await prefs.setStringList(key, cached);
  }

  static Future<List<Map<String, dynamic>>> getCachedSensorData(String device) async {
    final prefs = await SharedPreferences.getInstance();
    final key = '${_sensorKey}_$device';  // Fixed: Use '${_sensorKey}_$device' to avoid interpolation issues
    final cached = prefs.getStringList(key) ?? [];
    return cached.map((e) => json.decode(e) as Map<String, dynamic>).toList();
  }
}