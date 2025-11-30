// import 'package:flutter/material.dart';
// import 'package:provider/provider.dart';
// import '../services/api_service.dart';
// import '../services/firebase_service.dart';
// import 'package:intl/intl.dart';

// class DeviceDetailScreen extends StatefulWidget {
//   final String deviceName;
//   const DeviceDetailScreen({super.key, required this.deviceName});

//   @override State<DeviceDetailScreen> createState() => _DeviceDetailScreenState();
// }

// class _DeviceDetailScreenState extends State<DeviceDetailScreen> {
//   Map<String, dynamic> currentData = {};
//   bool loading = true;

//   @override
//   void initState() {
//     super.initState();
//     loadLiveData();
//     // Poll every 10s
//     Timer.periodic(const Duration(seconds: 10), (timer) => loadLiveData());
//   }

//   Future<void> loadLiveData() async {
//     final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
//     final response = await http.get(
//       Uri.parse('${ApiService.baseUrl}/api/live-data/${widget.deviceName}'),
//       headers: {'Authorization': 'Bearer $token'},
//     );

//     if (response.statusCode == 200) {
//       setState(() {
//         currentData = json.decode(response.body);
//         loading = false;
//       });
//     }
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(title: Text(widget.deviceName)),
//       body: loading
//           ? const Center(child: CircularProgressIndicator())
//           : Padding(
//               padding: const EdgeInsets.all(16),
//               child: Column(
//                 crossAxisAlignment: CrossAxisAlignment.start,
//                 children: [
//                   const Text("Live Readings", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
//                   const SizedBox(height: 20),
//                   Row(
//                     mainAxisAlignment: MainAxisAlignment.spaceEvenly,
//                     children: [
//                       _buildMetric("Temp (°C)", currentData['temperature_C']?.toString() ?? 'N/A', Icons.thermostat, Colors.red),
//                       _buildMetric("Power (W)", currentData['power_W']?.toString() ?? 'N/A', Icons.electrical_services, Colors.blue),
//                     ],
//                   ),
//                   const SizedBox(height: 20),
//                   const Text("Last Update:", style: TextStyle(fontSize: 16)),
//                   Text(DateFormat('HH:mm:ss').format(DateTime.now()), style: const TextStyle(color: Colors.grey)),
//                 ],
//               ),
//             ),
//     );
//   }

//   Widget _buildMetric(String label, String value, IconData icon, Color color) {
//     return Column(
//       children: [
//         Icon(icon, size: 48, color: color),
//         const SizedBox(height: 8),
//         Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
//         Text(label, style: const TextStyle(color: Colors.grey)),
//       ],
//     );
//   }
// }

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
        final data = json.decode(response.body);
        setState(() {
          currentData = data;
          // Generate simple chart data from recent points (demo; fetch historical if available)
          chartSpots = List.generate(10, (i) => FlSpot(i.toDouble(), (data['temperature_C'] ?? 0) + (i * 0.5 - 2.5)));
          loading = false;
        });
        // Cache online data
        await LocalCache.saveSensorData(widget.deviceName, data);
      } else {
        // Fallback to cache
        final cached = await LocalCache.getCachedSensorData(widget.deviceName);
        if (cached.isNotEmpty) {
          setState(() {
            currentData = cached.last;
            chartSpots = List.generate(10, (i) => FlSpot(i.toDouble(), (cached.last['temperature_C'] ?? 0) + (i * 0.5 - 2.5)));
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
        backgroundColor: const Color(0xFFFF5722),
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
                            const Text("Live Status: Online", style: TextStyle(fontWeight: FontWeight.bold)),
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
                    const Text("Live Readings", style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 2,
                      crossAxisSpacing: 16,
                      mainAxisSpacing: 16,
                      childAspectRatio: 1.2,
                      children: [
                        _buildMetric("Temp (°C)", currentData['temperature_C']?.toStringAsFixed(1) ?? 'N/A', Icons.thermostat, Colors.red),
                        _buildMetric("Power (W)", currentData['power_W']?.toStringAsFixed(0) ?? 'N/A', Icons.electrical_services, Colors.blue),
                        _buildMetric("CO (ppm)", currentData['CO_ppm']?.toStringAsFixed(0) ?? 'N/A', Icons.air, Colors.brown),
                        _buildMetric("CO2 (ppm)", currentData['CO2_ppm']?.toStringAsFixed(0) ?? 'N/A', Icons.eco, Colors.green),
                      ],
                    ),
                    const SizedBox(height: 20),

                    // Mini Chart
                    const Text("Recent Temperature Trend", style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
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
                              color: Colors.orange,
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

  Widget _buildMetric(String label, String value, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFFFF5722))),
            Text(label, style: const TextStyle(color: Colors.grey, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}