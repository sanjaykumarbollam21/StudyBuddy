import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../auth/controllers/auth_controller.dart';
import '../../auth/screens/login_screen.dart';
import '../../settings/screens/ai_settings_screen.dart';
import '../../settings/screens/diagnostics_screen.dart';

class ProfileTab extends StatefulWidget {
  final AuthController authController;
  final VoidCallback onToggleTheme;

  const ProfileTab({
    super.key,
    required this.authController,
    required this.onToggleTheme,
  });

  @override
  State<ProfileTab> createState() => _ProfileTabState();
}

class _ProfileTabState extends State<ProfileTab> {
  void _confirmLogout() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sign Out'),
        content: const Text('Are you sure you want to sign out of Study Buddy? Your learning progress is safely stored.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.rose),
            onPressed: () async {
              final nav = Navigator.of(context);
              nav.pop();
              await widget.authController.logout();
              if (mounted) {
                nav.pushAndRemoveUntil(
                  MaterialPageRoute(
                    builder: (_) => LoginScreen(authController: widget.authController),
                  ),
                  (route) => false,
                );
              }
            },
            child: const Text('Sign Out'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.authController.currentUser;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // User Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 36,
                        backgroundColor: AppColors.primary,
                        child: Text(
                          user?.displayName.substring(0, 1).toUpperCase() ?? 'S',
                          style: const TextStyle(fontSize: 28, color: Colors.white, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 18),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              user?.displayName ?? 'Student',
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              user?.email ?? 'student@studybuddy.ai',
                              style: const TextStyle(color: AppColors.lightTextSecondary, fontSize: 13),
                            ),
                            const SizedBox(height: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                              decoration: BoxDecoration(
                                color: AppColors.emerald.withAlpha(25),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                user?.profile?.educationLevel ?? 'Computer Science Undergraduate',
                                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.emerald),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Learning Preferences Section
              const Text('Learning Preferences', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.school_outlined, color: AppColors.primary),
                      title: const Text('Education Level'),
                      subtitle: Text(user?.profile?.educationLevel ?? 'Undergraduate'),
                      trailing: const Icon(Icons.chevron_right_rounded),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.lightbulb_outline_rounded, color: AppColors.primary),
                      title: const Text('Learning Style'),
                      subtitle: Text(user?.profile?.learningStyle ?? 'Visual & Practical'),
                      trailing: const Icon(Icons.chevron_right_rounded),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.timer_outlined, color: AppColors.primary),
                      title: const Text('Daily Study Goal'),
                      subtitle: Text('${((user?.profile?.dailyAvailableMins ?? 120) / 60).toStringAsFixed(1)} hours/day'),
                      trailing: const Icon(Icons.chevron_right_rounded),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // App Settings Section
              const Text('Application Settings', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Card(
                child: Column(
                  children: [
                    SwitchListTile(
                      secondary: Icon(
                        isDark ? Icons.dark_mode_rounded : Icons.light_mode_rounded,
                        color: AppColors.amber,
                      ),
                      title: const Text('Dark Mode'),
                      subtitle: Text(isDark ? 'Dark theme enabled' : 'Light theme enabled'),
                      value: isDark,
                      onChanged: (_) => widget.onToggleTheme(),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.smart_toy_outlined, color: AppColors.primary),
                      title: const Text('AI Intelligence Mode & Sync'),
                      subtitle: const Text('Offline / Hybrid / Online AI Settings'),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const AISettingsScreen(),
                          ),
                        );
                      },
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.analytics_outlined, color: AppColors.emerald),
                      title: const Text('Study Buddy Diagnostics'),
                      subtitle: const Text('Hardware, AI Engine, Storage & Health'),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => const DiagnosticsScreen(),
                          ),
                        );
                      },
                    ),
                    const Divider(height: 1),
                    const ListTile(
                      leading: Icon(Icons.record_voice_over_outlined, color: AppColors.primary),
                      title: Text('Voice Speed & Accent'),
                      subtitle: Text('Natural 1.0x (Alloy Academic)'),
                      trailing: Icon(Icons.chevron_right_rounded),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // Logout Button
              Center(
                child: TextButton.icon(
                  onPressed: _confirmLogout,
                  icon: const Icon(Icons.logout_rounded, color: AppColors.rose),
                  label: const Text('Sign Out', style: TextStyle(color: AppColors.rose, fontWeight: FontWeight.bold)),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
