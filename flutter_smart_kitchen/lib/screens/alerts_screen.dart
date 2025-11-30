// import 'package:flutter/material.dart';

// class AlertsScreen extends StatelessWidget {
//   const AlertsScreen({super.key});

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       appBar: AppBar(title: const Text("Alerts")),
//       body: const Center(child: Text("Alerts list here")),
//     );
//   }
// }


// Updated alerts_screen.dart - Implemented list with caching, badges, and swipe-to-dismiss for practicality
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/firebase_service.dart';
import '../services/local_cache.dart'; // Updated import
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/api_service.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  List<Map<String, dynamic>> alerts = [];
  bool loading = true;

  @override
  void initState() {
    super.initState();
    loadAlerts();
  }

  Future<void> loadAlerts() async {
    try {
      final token = Provider.of<AuthProvider>(context, listen: false).jwtToken!;
      final response = await http.get(
        Uri.parse('${ApiService.baseUrl}/api/alerts'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 200) {
        final List data = json.decode(response.body);
        setState(() {
          alerts = data.cast<Map<String, dynamic>>();
          loading = false;
        });
        // Cache alerts
        await LocalCache.saveAlerts(alerts);
      } else {
        // Fallback to cache
        final cached = await LocalCache.getCachedAlerts();
        setState(() {
          alerts = cached;
          loading = false;
        });
      }
    } catch (e) {
      final cached = await LocalCache.getCachedAlerts();
      setState(() {
        alerts = cached;
        loading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Loaded from cache: $e")),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Alerts"),
        backgroundColor: const Color(0xFFFF5722),
        foregroundColor: Colors.white,
        actions: [
          Badge(
            label: Text(alerts.length.toString()),
            isLabelVisible: alerts.isNotEmpty,
            child: IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: loadAlerts,
            ),
          ),
        ],
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: loadAlerts,
              child: alerts.isEmpty
                  ? const Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.notifications_off, size: 64, color: Colors.grey),
                          SizedBox(height: 16),
                          Text("No alerts yet. Your kitchen is safe!", style: TextStyle(fontSize: 18)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: alerts.length,
                      itemBuilder: (context, index) {
                        final alert = alerts[index];
                        return Dismissible(
                          key: Key(alert['id'].toString()),
                          direction: DismissDirection.endToStart,
                          background: Container(
                            padding: const EdgeInsets.only(right: 20),
                            alignment: Alignment.centerRight,
                            decoration: const BoxDecoration(
                              color: Colors.green,
                              borderRadius: BorderRadius.all(Radius.circular(8)),
                            ),
                            child: const Icon(Icons.check, color: Colors.white),
                          ),
                          onDismissed: (direction) {
                            // TODO: Mark as resolved via API
                            setState(() => alerts.removeAt(index));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text("Alert resolved")),
                            );
                          },
                          child: Card(
                            margin: const EdgeInsets.only(bottom: 12),
                            elevation: 2,
                            child: ListTile(
                              leading: const Icon(Icons.warning, color: Colors.red),
                              title: Text(alert['message'] ?? 'Unknown alert'),
                              subtitle: Text(alert['timestamp'] ?? DateTime.now().toString()),
                              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                              onTap: () {
                                // TODO: Navigate to details
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(content: Text("Viewing details for: ${alert['device']}")),
                                );
                              },
                            ),
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}