import 'package:flutter/foundation.dart';

class AppConfig {
  static const String appName = 'Study Buddy';
  static const String appTagline = 'Your AI Personal Teacher';
  static const String version = '1.0.0';

  // Base API configuration
  static String get baseUrl {
    if (kIsWeb) {
      return 'http://127.0.0.1:8000/api/v1';
    }
    // Android emulator special loopback
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    // Windows / macOS / iOS
    return 'http://127.0.0.1:8000/api/v1';
  }

  // Auth endpoints
  static String get signupEndpoint => '$baseUrl/auth/signup';
  static String get loginEndpoint => '$baseUrl/auth/login';
  static String get meEndpoint => '$baseUrl/auth/me';
  static String get forgotPasswordEndpoint => '$baseUrl/auth/forgot-password';

  // User endpoints
  static String get profileEndpoint => '$baseUrl/users/profile';
  static String get settingsEndpoint => '$baseUrl/users/settings';
  static String get notificationsEndpoint => '$baseUrl/users/notifications';
  static String get documentsEndpoint => '$baseUrl/documents';
}
