import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/firebase_service.dart';
import 'predictor_screen.dart';


class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final tenant = Provider.of<AuthProvider>(context).tenantId;
    return Scaffold(
      appBar: AppBar(title: const Text("Smart Kitchen"), actions: [
        IconButton(onPressed: () => Provider.of<AuthProvider>(context, listen: false).signOut(), icon: const Icon(Icons.logout))
      ]),
      body: Center(
        child: Column(
          children: [
            Text("Welcome Tenant: $tenant", style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 40),
            ElevatedButton(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const PredictorScreen())),
              child: const Text("Open Usage Predictor"),
            ),
          ],
        ),
      ),
    );
  }
}