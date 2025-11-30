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
  String insight = "AI predicts low risk—your home is protected!";

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
          spots = data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value['high_risk'] as double)).toList();  // Assuming 'high_risk' from API
          // Demo confidence
          confidenceSpots = spots.map((spot) => FlSpot(spot.x, spot.y + 0.1)).toList(); // Upper band example
          insight = "Predicted average risk: ${(data.map((d) => d['high_risk']).reduce((a, b) => a + b) / data.length).toStringAsFixed(2)}";
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
      spots = List.generate(7, (i) => FlSpot(i.toDouble(), 0.1 + i * 0.05 + (i % 2 == 0 ? 0.1 : -0.05)));  // Low risk probabilities
      confidenceSpots = spots.map((spot) => FlSpot(spot.x, spot.y + 0.1)).toList();
      insight = "🔮 Demo: 15% elevated risk next weekend—check smoke detectors!";
      loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Risk Predictor"),
        backgroundColor: const Color(0xFF1976D2),  // Blue insurance theme
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(  // Added to prevent overflow
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                "7-Day Property Risk Forecast",
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
                            color: const Color(0xFF1976D2),
                            dotData: const FlDotData(show: true),
                          ),
                          // Confidence band (simplified as another line)
                          LineChartBarData(
                            spots: confidenceSpots,
                            isCurved: true,
                            barWidth: 2,
                            color: Colors.blue.withOpacity(0.5),
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
                          Icon(Icons.security, color: Color(0xFF2196F3)),
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
                            const SnackBar(content: Text("Pro Tip: Install smoke alarms to reduce risk by 50%!")),
                          );
                        },
                        icon: const Icon(Icons.arrow_forward_ios, size: 14),
                        label: const Text("Get Risk Mitigation Tips"),
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