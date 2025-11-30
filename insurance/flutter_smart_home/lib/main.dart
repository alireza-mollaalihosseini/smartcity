// main.dart
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
// Removed unused FirebaseMessaging import

import 'package:smart_home_insurance/screens/login_screen.dart';
import 'package:smart_home_insurance/screens/home_screen.dart';
import 'package:smart_home_insurance/screens/alerts_screen.dart';
import 'package:smart_home_insurance/screens/predictor_screen.dart';
import 'package:smart_home_insurance/services/firebase_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Explicit Firebase options from your google-services.json (update for insurance project)
  const firebaseOptions = FirebaseOptions(
    apiKey: 'AIzaSyBKA-7BzXORO1hGCguW1OIwgVKTvQakbOA',  // Placeholder: Update with your insurance project API key
    appId: '1:3801295010:android:dd986937d98f2c18624ffb',  // Placeholder: Update with your insurance project app ID
    messagingSenderId: '3801295010',  // Placeholder: Update with your insurance project sender ID
    projectId: 'smart-home-insurance-demo',  // Updated for insurance project
    storageBucket: 'smart-home-insurance-demo.firebasestorage.app',  // Updated for insurance project
  );

  await Firebase.initializeApp(options: firebaseOptions);
  runApp(const SmartHomeInsuranceApp());
}

class SmartHomeInsuranceApp extends StatelessWidget {
  const SmartHomeInsuranceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: MaterialApp(
        title: 'Smart Home Insurance Demo',
        theme: ThemeData(
          primarySwatch: Colors.blue,  // Changed to blue for trust/insurance theme
          useMaterial3: true,
          scaffoldBackgroundColor: Colors.grey[50],
        ),
        home: const AuthWrapper(),
        debugShowCheckedModeBanner: false,
        routes: {
          '/home': (_) => const HomeScreen(),  // Home: Live sensors and risk overview
          '/alerts': (_) => const AlertsScreen(),  // Alerts: Property risk notifications
          '/predictions': (_) => const PredictorScreen(),  // Predictions: Risk forecasting
        },
      ),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        if (auth.isSignedIn) {
          return const HomeScreen();
        }
        return const LoginScreen();
      },
    );
  }
}