import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../auth/controllers/auth_controller.dart';
import 'home_tab.dart';
import 'learn_tab.dart';
import 'materials_tab.dart';
import 'practice_tab.dart';
import 'progress_tab.dart';
import 'profile_tab.dart';
import 'tutor_sheet.dart';
import '../../../core/notifications/notification_service.dart';
import '../../settings/screens/ai_settings_screen.dart';
import '../../agent/screens/autonomous_agent_screen.dart';

class MainShellScreen extends StatefulWidget {
  final AuthController authController;
  final VoidCallback? onToggleTheme;

  const MainShellScreen({
    super.key,
    required this.authController,
    this.onToggleTheme,
  });

  @override
  State<MainShellScreen> createState() => _MainShellScreenState();
}

class _MainShellScreenState extends State<MainShellScreen> {
  int _currentIndex = 0;

  void _onTabSelect(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  void _showNotifications() {
    final notifService = NotificationService();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => ListenableBuilder(
        listenable: notifService,
        builder: (context, _) {
          final items = notifService.notifications;
          return Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Expanded(
                      child: Text('Notifications & Reminders', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    ),
                    if (notifService.unreadCount > 0)
                      TextButton(
                        onPressed: () => notifService.markAllAsRead(),
                        child: const Text('Mark all read'),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                if (items.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Center(child: Text('No active notifications')),
                  )
                else
                  ...items.map((item) {
                    IconData icon;
                    Color color;
                    if (item.category == 'session_kickoff') {
                      icon = Icons.school_rounded;
                      color = AppColors.primary;
                    } else if (item.category == 'revision_due') {
                      icon = Icons.alarm_rounded;
                      color = AppColors.amber;
                    } else if (item.category == 'exam_alert') {
                      icon = Icons.warning_amber_rounded;
                      color = AppColors.rose;
                    } else {
                      icon = Icons.notifications_rounded;
                      color = AppColors.primary;
                    }

                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: CircleAvatar(
                        backgroundColor: color.withAlpha(30),
                        child: Icon(icon, color: color, size: 20),
                      ),
                      title: Text(
                        item.title,
                        style: TextStyle(
                          fontWeight: item.isRead ? FontWeight.normal : FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      subtitle: Text(item.message, style: const TextStyle(fontSize: 12)),
                      trailing: item.isRead
                          ? null
                          : IconButton(
                              icon: const Icon(Icons.check_circle_outline_rounded, size: 18),
                              onPressed: () => notifService.markAsRead(item.id),
                              tooltip: 'Mark as read',
                            ),
                    );
                  }),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tabs = [
      HomeTab(
        authController: widget.authController,
        onTabNavigate: _onTabSelect,
      ),
      const LearnTab(),
      const MaterialsTab(),
      const PracticeTab(),
      const ProgressTab(),
      ProfileTab(
        authController: widget.authController,
        onToggleTheme: widget.onToggleTheme ?? () {},
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.school_rounded, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 10),
            const Text(
              'Study Buddy',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.auto_awesome_rounded, color: AppColors.primary),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const AutonomousAgentScreen()),
              );
            },
            tooltip: 'Autonomous Study Agent',
          ),
          IconButton(
            icon: const Icon(Icons.tune_rounded),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const AISettingsScreen()),
              );
            },
            tooltip: 'AI Mode & Offline Sync',
          ),
          ListenableBuilder(
            listenable: NotificationService(),
            builder: (context, _) {
              final count = NotificationService().unreadCount;
              return IconButton(
                icon: count > 0
                    ? Badge(
                        label: Text('$count'),
                        child: const Icon(Icons.notifications_outlined),
                      )
                    : const Icon(Icons.notifications_outlined),
                onPressed: _showNotifications,
                tooltip: 'Notifications',
              );
            },
          ),
          const SizedBox(width: 8),
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: InkWell(
              onTap: () => _onTabSelect(5), // Jump to Profile
              borderRadius: BorderRadius.circular(20),
              child: CircleAvatar(
                radius: 16,
                backgroundColor: AppColors.primary.withAlpha(40),
                child: Text(
                  widget.authController.currentUser?.displayName.substring(0, 1).toUpperCase() ?? 'S',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary, fontSize: 13),
                ),
              ),
            ),
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: tabs,
      ),
      // Persistent AI Teacher Floating Action Button
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          TutorSheet.show(context);
        },
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.smart_toy_rounded, color: Colors.white),
        label: const Text(
          'Ask Study Buddy',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: _onTabSelect,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home_rounded),
            label: 'Home',
          ),
          NavigationDestination(
            icon: Icon(Icons.explore_outlined),
            selectedIcon: Icon(Icons.explore_rounded),
            label: 'Learn',
          ),
          NavigationDestination(
            icon: Icon(Icons.folder_outlined),
            selectedIcon: Icon(Icons.folder_rounded),
            label: 'Materials',
          ),
          NavigationDestination(
            icon: Icon(Icons.quiz_outlined),
            selectedIcon: Icon(Icons.quiz_rounded),
            label: 'Practice',
          ),
          NavigationDestination(
            icon: Icon(Icons.insights_outlined),
            selectedIcon: Icon(Icons.insights_rounded),
            label: 'Progress',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline_rounded),
            selectedIcon: Icon(Icons.person_rounded),
            label: 'Profile',
          ),
        ],
      ),
    );
  }
}
