// Updated lib/screens/home_screen.dart - Fixed tenant null handling
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/firebase_service.dart';
import 'predictor_screen.dart';
import 'device_detail_screen.dart';
import 'alerts_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  late List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    // Defer screen building to didChangeDependencies for safe Provider access
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final tenant = Provider.of<AuthProvider>(context).tenantId ?? 'Demo Tenant';
    _screens = [
      _buildDevicesOverview(tenant),
      const PredictorScreen(),
      const AlertsScreen(),
    ];
  }

  Widget _buildDevicesOverview(String tenant) {
    // Demo devices for product demo; replace with API fetch
    final devices = ['Smoke Detector', 'Water Sensor', 'Door Sensor', 'Temperature Sensor', 'Humidity Sensor', 'Motion Detector'];
    return Column(
      children: [
        // Welcome Header
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [const Color(0xFF2196F3).withOpacity(0.8), const Color(0xFF1976D2).withOpacity(0.8)],  // Blue insurance theme
            ),
            borderRadius: const BorderRadius.vertical(bottom: Radius.circular(20)),
          ),
          child: Column(
            children: [
              Text(
                "Welcome back, Policyholder!",
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.white),
              ),
              Text("Tenant: $tenant", style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 10),
              const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.security, color: Colors.white, size: 20),
                  SizedBox(width: 5),
                  Text("Your home is secure today", style: TextStyle(color: Colors.white70)),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Quick Actions
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ActionCard(icon: Icons.description, label: "View Policy", color: Colors.green),
              ActionCard(icon: Icons.assignment, label: "File Claim", color: Colors.blue),
              ActionCard(icon: Icons.support_agent, label: "Contact Agent", color: Colors.orange),
            ],
          ),
        ),
        const SizedBox(height: 20),

        // Devices List
        Expanded(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: ListView.builder(
              itemCount: devices.length,
              itemBuilder: (context, index) {
                final device = devices[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  elevation: 2,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  child: ListTile(
                    leading: Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: const Color(0xFF2196F3).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.home, color: Color(0xFF1976D2)),  // Home icon for smart home
                    ),
                    title: Text(device, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: () {
                      switch (device) {
                        case 'Smoke Detector':
                          return const Text("Status: Online • Smoke: 0ppm");
                        case 'Water Sensor':
                          return const Text("Status: Online • Moisture: 10%");
                        case 'Door Sensor':
                          return const Text("Status: Online • State: Closed");
                        case 'Temperature Sensor':
                          return const Text("Status: Online • Temp: 21°C");
                        case 'Humidity Sensor':
                          return const Text("Status: Online • Humidity: 50%");
                        case 'Motion Detector':
                          return const Text("Status: Online • Motion: None");
                        default:
                          return const Text("Status: Online");
                      }
                    }(),
                    trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (_) => DeviceDetailScreen(deviceName: device)),
                    ),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final tenant = Provider.of<AuthProvider>(context).tenantId ?? 'Demo Tenant';
    // Ensure screens are built if not already
    if (_screens.isEmpty) {
      _screens = [
        _buildDevicesOverview(tenant),
        const PredictorScreen(),
        const AlertsScreen(),
      ];
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text("Smart Home Insurance"),
        backgroundColor: const Color(0xFF1976D2),  // Blue theme
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            onPressed: () => Provider.of<AuthProvider>(context, listen: false).signOut(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() => _currentIndex = index),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: const Color(0xFF1976D2),  // Blue theme
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: "Home"),
          BottomNavigationBarItem(icon: Icon(Icons.show_chart), label: "Risk Predictor"),
          BottomNavigationBarItem(icon: Icon(Icons.notifications), label: "Alerts"),
        ],
      ),
    );
  }
}

// Helper Widget for Quick Actions
class ActionCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;

  const ActionCard({
    super.key,
    required this.icon,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        // TODO: Implement action
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Coming soon: $label")));
      },
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 32, color: color),
          ),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
        ],
      ),
    );
  }
}