// import 'dart:convert';
// import 'package:http/http.dart' as http;
// import 'package:fl_chart/fl_chart.dart';
// import 'package:flutter/material.dart';
// import 'package:provider/provider.dart';
// import '../services/api_service.dart';
// import '../services/firebase_service.dart';

// class PredictorScreen extends StatefulWidget {
//   const PredictorScreen({super.key});
//   @override State<PredictorScreen> createState() => _PredictorScreenState();
// }

// class _PredictorScreenState extends State<PredictorScreen> {
//   List<FlSpot> spots = [];
//   bool loading = true;

//   @override
//   void initState() {
//     super.initState();
//     loadPredictions();
//   }

//   Future<void> loadPredictions() async {
//     final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
//     // Replace with your real endpoint
//     final response = await http.get(
//       Uri.parse('${ApiService.baseUrl}/api/predictions'),
//       headers: {'Authorization': 'Bearer $token'},
//     );

//     if (response.statusCode == 200) {
//       final List data = json.decode(response.body);
//       setState(() {
//         spots = data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value['predicted_usage'] as double)).toList();
//         loading = false;
//       });
//     } else {
//       // Demo data if backend not ready
//       setState(() {
//         spots = List.generate(7, (i) => FlSpot(i.toDouble(), 10 + i * 3 + (i % 2 == 0 ? 5 : -3)));
//         loading = false;
//       });
//     }
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(title: const Text("Usage Predictor")),
//       body: Padding(
//         padding: const EdgeInsets.all(16),
//         child: Column(
//           children: [
//             const Text("7-Day Power Usage Forecast", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
//             const SizedBox(height: 20),
//             loading
//                 ? const CircularProgressIndicator()
//                 : SizedBox(
//                     height: 300,
//                     child: LineChart(
//                       LineChartData(
//                         gridData: const FlGridData(show: true),  // const kept (supported)
//                         titlesData: FlTitlesData(
//                           bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) => Text("${v.toInt() + 1}d"))),
//                           leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true)),
//                         ),
//                         borderData: FlBorderData(show: true),  // Removed const (not supported)
//                         lineBarsData: [
//                           LineChartBarData(
//                             spots: spots,
//                             isCurved: true,
//                             barWidth: 4,
//                             color: Colors.orange,
//                             dotData: const FlDotData(show: true),  // const kept (supported)
//                           ),
//                         ],
//                       ),
//                     ),
//                   ),
//             const SizedBox(height: 20),
//             const Card(
//               child: Padding(
//                 padding: EdgeInsets.all(16),  // Can add const if linter flags later
//                 child: Text("🔮 AI predicts 22% higher usage next weekend — schedule maintenance!", style: TextStyle(fontSize: 16)),
//               ),
//             ),
//           ],
//         ),
//       ),
//     );
//   }
// }

// // Updated predictor_screen.dart - Enhanced chart with confidence bands, more insights, and product tips
// import 'dart:convert';
// import 'package:fl_chart/fl_chart.dart';
// import 'package:http/http.dart' as http;
// import 'package:flutter/material.dart';
// import 'package:provider/provider.dart';
// import '../services/api_service.dart';
// import '../services/firebase_service.dart';

// class PredictorScreen extends StatefulWidget {
//   const PredictorScreen({super.key});
//   @override
//   State<PredictorScreen> createState() => _PredictorScreenState();
// }

// class _PredictorScreenState extends State<PredictorScreen> {
//   List<FlSpot> spots = [];
//   List<FlSpot> confidenceSpots = []; // For upper/lower bounds
//   bool loading = true;
//   String insight = "AI predicts steady usage—optimize your schedule!";

//   @override
//   void initState() {
//     super.initState();
//     loadPredictions();
//   }

//   Future<void> loadPredictions() async {
//     try {
//       final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
//       final response = await http.get(
//         Uri.parse('${ApiService.baseUrl}/api/predictions'),
//         headers: {'Authorization': 'Bearer $token'},
//       );

//       if (response.statusCode == 200) {
//         final List data = json.decode(response.body);
//         setState(() {
//           spots = data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value['predicted_usage'] as double)).toList();
//           // Demo confidence
//           confidenceSpots = spots.map((spot) => FlSpot(spot.x, spot.y + 2)).toList(); // Upper band example
//           insight = "Predicted average: ${(data.map((d) => d['predicted_usage']).reduce((a, b) => a + b) / data.length).toStringAsFixed(1)} kWh";
//           loading = false;
//         });
//       } else {
//         _loadDemoData();
//       }
//     } catch (e) {
//       _loadDemoData();
//     }
//   }

//   void _loadDemoData() {
//     setState(() {
//       spots = List.generate(7, (i) => FlSpot(i.toDouble(), 10 + i * 3 + (i % 2 == 0 ? 5 : -3)));
//       confidenceSpots = spots.map((spot) => FlSpot(spot.x, spot.y + 2)).toList();
//       insight = "🔮 Demo: 22% higher usage next weekend—schedule maintenance!";
//       loading = false;
//     });
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(
//         title: const Text("Usage Predictor"),
//         backgroundColor: const Color(0xFFFF5722),
//         foregroundColor: Colors.white,
//       ),
//       body: Padding(
//         padding: const EdgeInsets.all(16),
//         child: Column(
//           crossAxisAlignment: CrossAxisAlignment.start,
//           children: [
//             const Text(
//               "7-Day Power Usage Forecast",
//               style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
//             ),
//             const SizedBox(height: 20),
//             SizedBox(
//               height: 300,
//               child: Stack(
//                 children: [
//                   LineChart(
//                     LineChartData(
//                       gridData: const FlGridData(show: true),
//                       titlesData: FlTitlesData(
//                         bottomTitles: AxisTitles(
//                           sideTitles: SideTitles(
//                             showTitles: true,
//                             getTitlesWidget: (value, meta) => Text("${value.toInt() + 1}D", style: const TextStyle(fontSize: 10)),
//                           ),
//                         ),
//                         leftTitles: AxisTitles(
//                           sideTitles: SideTitles(showTitles: true, reservedSize: 40),
//                         ),
//                       ),
//                       borderData: FlBorderData(show: true),
//                       lineBarsData: [
//                         LineChartBarData(
//                           spots: spots,
//                           isCurved: true,
//                           barWidth: 4,
//                           color: const Color(0xFFFF5722),
//                           dotData: const FlDotData(show: true),
//                         ),
//                         // Confidence band (simplified as another line)
//                         LineChartBarData(
//                           spots: confidenceSpots,
//                           isCurved: true,
//                           barWidth: 2,
//                           color: Colors.orange.withOpacity(0.5),
//                           dotData: const FlDotData(show: false),
//                         ),
//                       ],
//                     ),
//                   ),
//                   if (loading) const Center(child: CircularProgressIndicator()),
//                 ],
//               ),
//             ),
//             const SizedBox(height: 20),

//             // Insights Cards
//             Card(
//               elevation: 2,
//               child: Padding(
//                 padding: const EdgeInsets.all(16),
//                 child: Column(
//                   crossAxisAlignment: CrossAxisAlignment.start,
//                   children: [
//                     const Row(
//                       children: [
//                         Icon(Icons.lightbulb, color: Color(0xFFFFA726)),
//                         SizedBox(width: 8),
//                         Text("AI Insight", style: TextStyle(fontWeight: FontWeight.bold)),
//                       ],
//                     ),
//                     const SizedBox(height: 8),
//                     Text(insight, style: const TextStyle(fontSize: 16)),
//                     const SizedBox(height: 8),
//                     TextButton.icon(
//                       onPressed: () {
//                         // TODO: Navigate to tips or schedule
//                         ScaffoldMessenger.of(context).showSnackBar(
//                           const SnackBar(content: Text("Pro Tip: Unplug unused devices to save 15%!")),
//                         );
//                       },
//                       icon: const Icon(Icons.arrow_forward_ios, size: 14),
//                       label: const Text("Get Optimization Tips"),
//                     ),
//                   ],
//                 ),
//               ),
//             ),
//           ],
//         ),
//       ),
//     );
//   }
// }


// Updated lib/screens/predictor_screen.dart - Wrapped Column in SingleChildScrollView to fix overflow
import 'dart:convert';
import 'package:fl_chart/fl_chart.dart';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/firebase_service.dart';

class PredictorScreen extends StatefulWidget {
  const PredictorScreen({super.key});
  @override
  State<PredictorScreen> createState() => _PredictorScreenState();
}

class _PredictorScreenState extends State<PredictorScreen> {
  List<FlSpot> spots = [];
  List<FlSpot> confidenceSpots = []; // For upper/lower bounds
  bool loading = true;
  String insight = "AI predicts steady usage—optimize your schedule!";

  @override
  void initState() {
    super.initState();
    loadPredictions();
  }

  Future<void> loadPredictions() async {
    try {
      final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/predictions'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List data = json.decode(response.body);
        setState(() {
          spots = data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value['predicted_usage'] as double)).toList();
          // Demo confidence
          confidenceSpots = spots.map((spot) => FlSpot(spot.x, spot.y + 2)).toList(); // Upper band example
          insight = "Predicted average: ${(data.map((d) => d['predicted_usage']).reduce((a, b) => a + b) / data.length).toStringAsFixed(1)} kWh";
          loading = false;
        });
      } else {
        _loadDemoData();
      }
    } catch (e) {
      _loadDemoData();
    }
  }

  void _loadDemoData() {
    setState(() {
      spots = List.generate(7, (i) => FlSpot(i.toDouble(), 10 + i * 3 + (i % 2 == 0 ? 5 : -3)));
      confidenceSpots = spots.map((spot) => FlSpot(spot.x, spot.y + 2)).toList();
      insight = "🔮 Demo: 22% higher usage next weekend—schedule maintenance!";
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Usage Predictor"),
        backgroundColor: const Color(0xFFFF5722),
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(  // Added to prevent overflow
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "7-Day Power Usage Forecast",
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              SizedBox(
                height: 300,
                child: Stack(
                  children: [
                    LineChart(
                      LineChartData(
                        gridData: const FlGridData(show: true),
                        titlesData: FlTitlesData(
                          bottomTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              getTitlesWidget: (value, meta) => Text("${value.toInt() + 1}D", style: const TextStyle(fontSize: 10)),
                            ),
                          ),
                          leftTitles: AxisTitles(
                            sideTitles: SideTitles(showTitles: true, reservedSize: 40),
                          ),
                        ),
                        borderData: FlBorderData(show: true),
                        lineBarsData: [
                          LineChartBarData(
                            spots: spots,
                            isCurved: true,
                            barWidth: 4,
                            color: const Color(0xFFFF5722),
                            dotData: const FlDotData(show: true),
                          ),
                          // Confidence band (simplified as another line)
                          LineChartBarData(
                            spots: confidenceSpots,
                            isCurved: true,
                            barWidth: 2,
                            color: Colors.orange.withOpacity(0.5),
                            dotData: const FlDotData(show: false),
                          ),
                        ],
                      ),
                    ),
                    if (loading) const Center(child: CircularProgressIndicator()),
                  ],
                ),
              ),
              const SizedBox(height: 20),

              // Insights Cards
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.lightbulb, color: Color(0xFFFFA726)),
                          SizedBox(width: 8),
                          Text("AI Insight", style: TextStyle(fontWeight: FontWeight.bold)),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(insight, style: const TextStyle(fontSize: 16)),
                      const SizedBox(height: 8),
                      TextButton.icon(
                        onPressed: () {
                          // TODO: Navigate to tips or schedule
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Pro Tip: Unplug unused devices to save 15%!")),
                          );
                        },
                        icon: const Icon(Icons.arrow_forward_ios, size: 14),
                        label: const Text("Get Optimization Tips"),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),  // Added extra space at bottom for scroll padding
            ],
          ),
        ),
      ),
    );
  }
}