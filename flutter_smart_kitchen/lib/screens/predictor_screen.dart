import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/firebase_service.dart';

class PredictorScreen extends StatefulWidget {
  const PredictorScreen({super.key});
  @override State<PredictorScreen> createState() => _PredictorScreenState();
}

class _PredictorScreenState extends State<PredictorScreen> {
  List<FlSpot> spots = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    loadPredictions();
  }

  Future<void> loadPredictions() async {
    final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
    // Replace with your real endpoint
    final response = await http.get(
      Uri.parse('${ApiService.baseUrl}/api/predictions'),
      headers: {'Authorization': 'Bearer $token'},
    );

    if (response.statusCode == 200) {
      final List data = json.decode(response.body);
      setState(() {
        spots = data.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value['predicted_usage'] as double)).toList();
        loading = false;
      });
    } else {
      // Demo data if backend not ready
      setState(() {
        spots = List.generate(7, (i) => FlSpot(i.toDouble(), 10 + i * 3 + (i % 2 == 0 ? 5 : -3)));
        loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Usage Predictor")),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            const Text("7-Day Power Usage Forecast", style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            loading
                ? const CircularProgressIndicator()
                : SizedBox(
                    height: 300,
                    child: LineChart(
                      LineChartData(
                        gridData: const FlGridData(show: true),
                        titlesData: FlTitlesData(
                          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) => Text("${v.toInt() + 1}d"))),
                          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true)),
                        ),
                        borderData: FlBorderData(show: true),
                        lineBarsData: [
                          LineChartBarData(
                            spots: spots,
                            isCurved: true,
                            barWidth: 4,
                            color: Colors.orange,
                            dotData: const FlDotData(show: true),
                          ),
                        ],
                      ),
                    ),
                  ),
            const SizedBox(height: 20),
            const Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Text("🔮 AI predicts 22% higher usage next weekend — schedule maintenance!", style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}