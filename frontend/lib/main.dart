import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/controllers/auth_controller.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/auth/screens/onboarding_screen.dart';
import 'features/dashboard/screens/main_shell_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final authController = AuthController();
  await authController.initialize();
  runApp(StudyBuddyApp(authController: authController));
}

class StudyBuddyApp extends StatefulWidget {
  final AuthController authController;

  const StudyBuddyApp({super.key, required this.authController});

  @override
  State<StudyBuddyApp> createState() => _StudyBuddyAppState();
}

class _StudyBuddyAppState extends State<StudyBuddyApp> {
  ThemeMode _themeMode = ThemeMode.system;

  void _toggleTheme() {
    setState(() {
      if (_themeMode == ThemeMode.light) {
        _themeMode = ThemeMode.dark;
      } else if (_themeMode == ThemeMode.dark) {
        _themeMode = ThemeMode.light;
      } else {
        // If system, toggle based on current platform brightness
        final brightness = WidgetsBinding.instance.platformDispatcher.platformBrightness;
        _themeMode = brightness == Brightness.dark ? ThemeMode.light : ThemeMode.dark;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Study Buddy',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: _themeMode,
      home: ListenableBuilder(
        listenable: widget.authController,
        builder: (context, _) {
          if (!widget.authController.isInitialized) {
            return const Scaffold(
              body: Center(
                child: CircularProgressIndicator(),
              ),
            );
          }

          if (!widget.authController.isAuthenticated) {
            return LoginScreen(authController: widget.authController);
          }

          final user = widget.authController.currentUser;
          if (user != null && !user.isOnboardingCompleted) {
            return OnboardingScreen(authController: widget.authController);
          }

          return MainShellScreen(
            authController: widget.authController,
            onToggleTheme: _toggleTheme,
          );
        },
      ),
    );
  }
}
