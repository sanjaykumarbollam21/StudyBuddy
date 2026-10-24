import 'package:flutter/material.dart';

class AppColors {
  // Brand Primary & Secondary (Deep academic navy & electric indigo)
  static const Color primary = Color(0xFF4F46E5); // Indigo 600
  static const Color primaryLight = Color(0xFF818CF8); // Indigo 400
  static const Color primaryDark = Color(0xFF3730A3); // Indigo 800

  static const Color secondary = Color(0xFF0F172A); // Slate 900
  static const Color secondaryLight = Color(0xFF1E293B); // Slate 800

  // Accent Colors for learning states & mastery
  static const Color amber = Color(0xFFF59E0B); // Amber 500 (Streak, in-progress)
  static const Color amberLight = Color(0xFFFEF3C7);
  static const Color emerald = Color(0xFF10B981); // Emerald 500 (Mastered, correct)
  static const Color emeraldLight = Color(0xFFD1FAE5);
  static const Color rose = Color(0xFFF43F5E); // Rose 500 (Weak area, alerts)
  static const Color roseLight = Color(0xFFFFE4E6);
  static const Color sky = Color(0xFF0284C7); // Sky 600 (Informational)
  static const Color purple = Color(0xFF9333EA); // Purple 600

  // Light theme neutrals
  static const Color lightBg = Color(0xFFF8FAFC); // Slate 50
  static const Color lightSurface = Color(0xFFFFFFFF);
  static const Color lightSurfaceAlt = Color(0xFFF1F5F9); // Slate 100
  static const Color lightTextPrimary = Color(0xFF0F172A); // Slate 900
  static const Color lightTextSecondary = Color(0xFF64748B); // Slate 500
  static const Color lightBorder = Color(0xFFE2E8F0); // Slate 200

  // Dark theme neutrals
  static const Color darkBg = Color(0xFF0B0F17);
  static const Color darkSurface = Color(0xFF161F30);
  static const Color darkSurfaceAlt = Color(0xFF1E293B);
  static const Color darkTextPrimary = Color(0xFFF8FAFC);
  static const Color darkTextSecondary = Color(0xFF94A3B8);
  static const Color darkBorder = Color(0xFF334155);
}
