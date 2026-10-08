import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/main.dart';
import 'package:frontend/features/auth/controllers/auth_controller.dart';
import 'package:frontend/features/auth/screens/login_screen.dart';
import 'package:frontend/features/dashboard/screens/main_shell_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('Renders Login Screen when unauthenticated', (WidgetTester tester) async {
    final authController = AuthController();
    await authController.initialize();

    await tester.pumpWidget(StudyBuddyApp(authController: authController));
    await tester.pumpAndSettle();

    expect(find.text('Welcome to Study Buddy'), findsOneWidget);
    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.text('Sign In'), findsOneWidget);
    expect(find.text('Quick Start: Demo Student Mode'), findsOneWidget);
  });

  testWidgets('Renders Main Shell and Home Tab when logged in with Demo Student', (WidgetTester tester) async {
    final authController = AuthController();
    await authController.initialize();
    await authController.loginWithDemoAccount();

    await tester.pumpWidget(StudyBuddyApp(authController: authController));
    await tester.pumpAndSettle();

    expect(find.byType(MainShellScreen), findsOneWidget);
    expect(find.textContaining('Sanjay'), findsWidgets);
    expect(find.text('Ask Study Buddy'), findsWidgets);
    expect(find.text("Today's Learning Plan"), findsOneWidget);
    expect(find.text('Upload Material'), findsOneWidget);
  });
}
