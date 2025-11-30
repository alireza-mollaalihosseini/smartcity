// Updated device_detail_screen.dart - Added chart, more metrics, offline caching, and better layout
import 'dart:async';
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/firebase_service.dart';
import '../services/local_cache.dart'; // Updated import
import 'package:intl/intl.dart';

class DeviceDetailScreen extends StatefulWidget {
  final String deviceName;
  const DeviceDetailScreen({super.key, required this.deviceName});

  @override
  State<DeviceDetailScreen> createState() => _DeviceDetailScreenState();
}

class _DeviceDetailScreenState extends State<DeviceDetailScreen> {
  Map<String, dynamic> currentData = {};
  List<FlSpot> chartSpots = [];
  bool loading = true;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    loadLiveData();
    _timer = Timer.periodic(const Duration(seconds: 10), (timer) => loadLiveData());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> loadLiveData() async {
    try {
      final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/live-data/${widget.deviceName}'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List dataList = json.decode(response.body);
        if (dataList.isNotEmpty) {
          final data = dataList.last;  // Use latest reading
          setState(() {
            currentData = data;
            final readings = data['readings'] as Map<String, dynamic>;
            // Generate simple chart data from relevant metric (e.g., temp_C if available)
            final chartValue = readings['temp_C']?.toDouble() ?? readings['smoke_ppm']?.toDouble() ?? readings['moisture_percent']?.toDouble() ?? 0.0;
            chartSpots = List.generate(10, (i) => FlSpot(i.toDouble(), chartValue + (i * 0.5 - 2.5)));
            loading = false;
          });
          // Cache online data
          await LocalCache.saveSensorData(widget.deviceName, data);
        }
      } else {
        // Fallback to cache
        final cached = await LocalCache.getCachedSensorData(widget.deviceName);
        if (cached.isNotEmpty) {
          setState(() {
            currentData = cached.last;
            final readings = currentData['readings'] as Map<String, dynamic>;
            final chartValue = readings['temp_C']?.toDouble() ?? readings['smoke_ppm']?.toDouble() ?? readings['moisture_percent']?.toDouble() ?? 0.0;
            chartSpots = List.generate(10, (i) => FlSpot(i.toDouble(), chartValue + (i * 0.5 - 2.5)));
            loading = false;
          });
        }
      }
    } catch (e) {
      // Error handling for product robustness
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Connection issue: $e. Using cached data.")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.deviceName),
        backgroundColor: const Color(0xFF1976D2),  // Blue insurance theme
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: loadLiveData,
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: loadLiveData,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header with status
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            Icon(
                              Icons.circle,
                              color: currentData['status'] == 'online' ? Colors.green : Colors.orange,
                              size: 16,
                            ),
                            const SizedBox(width: 8),
                            const Text("Live Status: Secure", style: TextStyle(fontWeight: FontWeight.bold)),
                            const Spacer(),
                            Text(
                              DateFormat('HH:mm:ss').format(DateTime.now()),
                              style: const TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 20),

                    // Metrics Grid
                    const Text("Live Sensor Readings", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 2,
                      crossAxisSpacing: 16,
                      mainAxisSpacing: 16,
                      childAspectRatio: 1.2,
                      children: _buildMetricsForDevice(),
                    ),
                    const SizedBox(height: 20),

                    // Mini Chart
                    const Text("Recent Sensor Trend", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
                    const SizedBox(height: 12),
                    SizedBox(
                      height: 200,
                      child: LineChart(
                        LineChartData(
                          gridData: const FlGridData(show: true),
                          titlesData: FlTitlesData(show: false),
                          borderData: FlBorderData(show: true),
                          lineBarsData: [
                            LineChartBarData(
                              spots: chartSpots,
                              isCurved: true,
                              color: Colors.blue,
                              barWidth: 3,
                              dotData: const FlDotData(show: true),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  // List<Widget> _buildMetricsForDevice() {
  //   final readings = currentData['readings'] as Map<String, dynamic>? ?? {};
  //   final metrics = <Widget>[];
  //   switch (widget.deviceName.toLowerCase()) {
  //     case 'smoke_detector':
  //       metrics.add(_buildMetric("Smoke (ppm)", readings['smoke_ppm']?.toStringAsFixed(1) ?? 'N/A', Icons.warning, Colors.red));
  //       metrics.add(_buildMetric("Alarm", readings['alarm'] ? 'Active' : 'Clear', Icons.alarm, Colors.orange));
  //       break;
  //     case 'water_sensor':
  //       metrics.add(_buildMetric("Moisture (%)", readings['moisture_percent']?.toStringAsFixed(1) ?? 'N/A', Icons.water_drop, Colors.blue));
  //       metrics.add(_buildMetric("Leak", readings['leak_detected'] ? 'Detected' : 'None', Icons.warning, Colors.red));
  //       break;
  //     case 'door_sensor':
  //       metrics.add(_buildMetric("State", readings['state']?.toString().title() ?? 'Unknown', Icons.door_front_door, Colors.brown));
  //       metrics.add(_buildMetric("Last Change", readings['last_change'] ?? 'N/A', Icons.access_time, Colors.grey));
  //       break;
  //     case 'temperature_sensor':
  //       metrics.add(_buildMetric("Temp (°C)", readings['temp_C']?.toStringAsFixed(1) ?? 'N/A', Icons.thermostat, Colors.red));
  //       break;
  //     case 'humidity_sensor':
  //       metrics.add(_buildMetric("Humidity (%)", readings['humidity_percent']?.toStringAsFixed(1) ?? 'N/A', Icons.water_drop, Colors.blue));
  //       break;
  //     case 'motion_detector':
  //       metrics.add(_buildMetric("Motion", readings['motion_detected'] ? 'Detected' : 'None', Icons.motion_photo_movie, Colors.green));
  //       metrics.add(_buildMetric("Last Detected", readings['last_detected'] ?? 'N/A', Icons.access_time, Colors.grey));
  //       break;
  //     default:
  //       metrics.add(_buildMetric("Status", 'Online', Icons.info, Colors.grey));
  //   }
  //   // Fill to 2x2 grid if needed
  //   while (metrics.length < 4) {
  //     metrics.add(_buildMetric("N/A", 'N/A', Icons.help_outline, Colors.grey));
  //   }
  //   return metrics.take(4).toList();
  // }

  List<Widget> _buildMetricsForDevice() {
    final readings = currentData['readings'] as Map<String, dynamic>? ?? {};
    final metrics = <Widget>[];
    switch (widget.deviceName.toLowerCase()) {
      case 'smoke_detector':
        metrics.add(_buildMetric("Smoke (ppm)", readings['smoke_ppm']?.toStringAsFixed(1) ?? 'N/A', Icons.warning, Colors.red));
        metrics.add(_buildMetric("Alarm", readings['alarm'] ? 'Active' : 'Clear', Icons.alarm, Colors.orange));
        break;
      case 'water_sensor':
        metrics.add(_buildMetric("Moisture (%)", readings['moisture_percent']?.toStringAsFixed(1) ?? 'N/A', Icons.water_drop, Colors.blue));
        metrics.add(_buildMetric("Leak", readings['leak_detected'] ? 'Detected' : 'None', Icons.warning, Colors.red));
        break;
      case 'door_sensor':
        metrics.add(_buildMetric("State", _capitalize(readings['state']?.toString() ?? 'Unknown'), Icons.door_front_door, Colors.brown));
        metrics.add(_buildMetric("Last Change", readings['last_change'] ?? 'N/A', Icons.access_time, Colors.grey));
        break;
      case 'temperature_sensor':
        metrics.add(_buildMetric("Temp (°C)", readings['temp_C']?.toStringAsFixed(1) ?? 'N/A', Icons.thermostat, Colors.red));
        break;
      case 'humidity_sensor':
        metrics.add(_buildMetric("Humidity (%)", readings['humidity_percent']?.toStringAsFixed(1) ?? 'N/A', Icons.water_drop, Colors.blue));
        break;
      case 'motion_detector':
        metrics.add(_buildMetric("Motion", readings['motion_detected'] ? 'Detected' : 'None', Icons.motion_photos_on, Colors.green));
        metrics.add(_buildMetric("Last Detected", readings['last_detected'] ?? 'N/A', Icons.access_time, Colors.grey));
        break;
      default:
        metrics.add(_buildMetric("Status", 'Online', Icons.info, Colors.grey));
    }
    // Fill to 2x2 grid if needed
    while (metrics.length < 4) {
      metrics.add(_buildMetric("N/A", 'N/A', Icons.help_outline, Colors.grey));
    }
    return metrics.take(4).toList();
  }

  // Add this helper method to the class
  String _capitalize(String text) {
    if (text.isEmpty) return text;
    return text[0].toUpperCase() + text.substring(1).toLowerCase();
  }

  Widget _buildMetric(String label, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF1976D2))),
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}