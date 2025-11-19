import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/firebase_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController(text: "demo@customer.com");
  final _passwordController = TextEditingController(text: "demo123");
  bool _loading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.kitchen, size: 100, color: Colors.orange),
            const Text("Smart Kitchen", style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
            const SizedBox(height: 48),
            TextField(controller: _emailController, decoration: const InputDecoration(labelText: "Email")),
            TextField(controller: _passwordController, decoration: const InputDecoration(labelText: "Password"), obscureText: true),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _loading ? null : () async {
                  setState(() => _loading = true);
                  final success = await Provider.of<AuthProvider>(context, listen: false)
                      .signIn(_emailController.text, _passwordController.text);
                  setState(() => _loading = false);
                  if (!success) {
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Login failed")));
                  }
                },
                child: _loading ? const CircularProgressIndicator() : const Text("Login"),
              ),
            ),
          ],
        ),
      ),
    );
  }
}