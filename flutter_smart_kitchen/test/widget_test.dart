// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

// import 'package:flutter/material.dart';
// import 'package:flutter_test/flutter_test.dart';

// import 'package:flutter_smart_kitchen/main.dart';

// void main() {
//   testWidgets('Counter increments smoke test', (WidgetTester tester) async {
//     // Build our app and trigger a frame.
//     await tester.pumpWidget(const MyApp());

//     // Verify that our counter starts at 0.
//     expect(find.text('0'), findsOneWidget);
//     expect(find.text('1'), findsNothing);

//     // Tap the '+' icon and trigger a frame.
//     await tester.tap(find.byIcon(Icons.add));
//     await tester.pump();

//     // Verify that our counter has incremented.
//     expect(find.text('0'), findsNothing);
//     expect(find.text('1'), findsOneWidget);
//   });
// }


// test/widget_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:smart_kitchen/main.dart';
import 'mocks/mock_auth_provider.dart';  // Mock provider

void main() {
  Widget buildTestApp({bool signedIn = false}) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => MockAuthProvider().._isSignedIn = signedIn),  // Mock, optional signed-in state
      ],
      child: const SmartKitchenApp(),
    );
  }

  testWidgets('App launches and shows login screen smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(buildTestApp());

    // Expect login screen (unauthenticated)
    expect(find.text('Smart Kitchen'), findsOneWidget);
    expect(find.byIcon(Icons.kitchen), findsOneWidget);
    expect(find.byType(TextField), findsNWidgets(2));  // Email + password
    expect(find.text('Login'), findsOneWidget);

    // No home screen
    expect(find.text('Welcome Tenant:'), findsNothing);
  });

  testWidgets('App shows home screen when signed in', (WidgetTester tester) async {
    await tester.pumpWidget(buildTestApp(signedIn: true));

    // Expect home screen
    expect(find.text('Smart Kitchen'), findsOneWidget);  // AppBar
    expect(find.text('Welcome Tenant: test-tenant'), findsOneWidget);
    expect(find.text('Open Usage Predictor'), findsOneWidget);
    expect(find.byIcon(Icons.logout), findsOneWidget);
  });

  testWidgets('Login button shows loading state', (WidgetTester tester) async {
    await tester.pumpWidget(buildTestApp());

    // Initial state
    expect(find.text('Login'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);

    // Simulate tap (triggers _loading = true via setState)
    await tester.enterText(find.byType(TextField).first, 'test@example.com');
    await tester.enterText(find.byType(TextField).last, 'password');
    await tester.tap(find.text('Login'));
    await tester.pump();  // Pump after tap to trigger onPressed

    // Loading state
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Login'), findsNothing);  // Button child changes

    // Simulate completion (pumpAndSettle waits for async, but mock is sync)
    await tester.pumpAndSettle();
    expect(find.text('Login'), findsOneWidget);  // Back to normal
  });
}