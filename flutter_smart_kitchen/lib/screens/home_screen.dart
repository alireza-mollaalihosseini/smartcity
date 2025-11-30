// import 'package:flutter/material.dart';
// import 'package:provider/provider.dart';
// import '../services/firebase_service.dart';
// import 'predictor_screen.dart';


// class HomeScreen extends StatelessWidget {
//   const HomeScreen({super.key});

//   @override
//   Widget build(BuildContext context) {
//     final tenant = Provider.of<AuthProvider>(context).tenantId;
//     return Scaffold(
//       appBar: AppBar(title: const Text("Smart Kitchen"), actions: [
//         IconButton(onPressed: () => Provider.of<AuthProvider>(context, listen: false).signOut(), icon: const Icon(Icons.logout))
//       ]),
//       body: Center(
//         child: Column(
//           children: [
//             Text("Welcome Tenant: $tenant", style: Theme.of(context).textTheme.headlineSmall),
//             const SizedBox(height: 40),
//             ElevatedButton(
//               onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PredictorScreen())),
//               child: const Text("Open Usage Predictor"),
//             ),
//           ],
//         ),
//       ),
//     );
//   }
// }

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
    final devices = ['Refrigerator', 'Oven', 'Microwave'];
    return Column(
      children: [
        // Welcome Header
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [const Color(0xFFFFA726).withOpacity(0.8), const Color(0xFFFF7043).withOpacity(0.8)],
            ),
            borderRadius: const BorderRadius.vertical(bottom: Radius.circular(20)),
          ),
          child: Column(
            children: [
              Text(
                "Welcome back, Kitchen Master!",
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: Colors.white),
              ),
              Text("Tenant: $tenant", style: const TextStyle(color: Colors.white70)),
              const SizedBox(height: 10),
              const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.trending_up, color: Colors.white, size: 20),
                  SizedBox(width: 5),
                  Text("Everything looks safe today", style: TextStyle(color: Colors.white70)),
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
              ActionCard(icon: Icons.add_alert, label: "Set Alert", color: Colors.green),
              ActionCard(icon: Icons.settings, label: "Settings", color: Colors.blue),
              ActionCard(icon: Icons.help, label: "Support", color: Colors.orange),
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
                        color: const Color(0xFFFFA726).withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.kitchen, color: Color(0xFFFF5722)),
                    ),
                    title: Text(device, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: const Text("Status: Online • Temp: 4°C"),
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
        title: const Text("Smart Kitchen"),
        backgroundColor: const Color(0xFFFF5722),
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
        selectedItemColor: const Color(0xFFFF5722),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: "Home"),
          BottomNavigationBarItem(icon: Icon(Icons.show_chart), label: "Predictor"),
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