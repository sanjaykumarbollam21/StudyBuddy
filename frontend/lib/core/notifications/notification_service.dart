import 'package:flutter/foundation.dart';

class StudyNotification {
  final String id;
  final String title;
  final String message;
  final String category; // session_kickoff, revision_due, exam_alert, system
  final String? actionRoute;
  final DateTime createdAt;
  bool isRead;
  final String priority; // low, medium, high, urgent

  StudyNotification({
    required this.id,
    required this.title,
    required this.message,
    required this.category,
    this.actionRoute,
    DateTime? createdAt,
    this.isRead = false,
    this.priority = 'medium',
  }) : createdAt = createdAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'message': message,
    'category': category,
    'action_route': actionRoute,
    'created_at': createdAt.toIso8601String(),
    'is_read': isRead,
    'priority': priority,
  };

  factory StudyNotification.fromJson(Map<String, dynamic> json) => StudyNotification(
    id: json['id'] as String,
    title: json['title'] as String,
    message: json['message'] as String,
    category: json['category'] as String,
    actionRoute: json['action_route'] as String?,
    createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : null,
    isRead: json['is_read'] as bool? ?? false,
    priority: json['priority'] as String? ?? 'medium',
  );
}

class NotificationService extends ChangeNotifier {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal() {
    _seedDefaultNotifications();
  }

  final List<StudyNotification> _notifications = [];

  List<StudyNotification> get notifications => List.unmodifiable(_notifications);
  int get unreadCount => _notifications.where((n) => !n.isRead).length;

  void _seedDefaultNotifications() {
    _notifications.addAll([
      StudyNotification(
        id: 'notif-default-1',
        title: 'Study Session Kickoff 🚀',
        message: 'Your 30-minute study session is starting. Ready to continue Deadlocks?',
        category: 'session_kickoff',
        actionRoute: '/teaching',
        priority: 'high',
      ),
      StudyNotification(
        id: 'notif-default-2',
        title: 'Spaced Revision Due ⏰',
        message: 'You have 4 revision items due today in Operating Systems.',
        category: 'revision_due',
        actionRoute: '/revision',
        priority: 'medium',
      ),
      StudyNotification(
        id: 'notif-default-3',
        title: 'Exam Countdown Alert 🎯',
        message: 'Your OS exam is 5 days away. Synchronization is still below your target mastery.',
        category: 'exam_alert',
        actionRoute: '/exam',
        priority: 'urgent',
      ),
    ]);
  }

  void markAsRead(String id) {
    final idx = _notifications.indexWhere((n) => n.id == id);
    if (idx != -1) {
      _notifications[idx].isRead = true;
      notifyListeners();
    }
  }

  void markAllAsRead() {
    for (var n in _notifications) {
      n.isRead = true;
    }
    notifyListeners();
  }

  void addNotification(StudyNotification notification) {
    _notifications.insert(0, notification);
    notifyListeners();
  }

  void generateProactiveAlert({
    required String title,
    required String message,
    required String category,
    String? actionRoute,
    String priority = 'medium',
  }) {
    final notif = StudyNotification(
      id: 'notif-${DateTime.now().millisecondsSinceEpoch}',
      title: title,
      message: message,
      category: category,
      actionRoute: actionRoute,
      priority: priority,
    );
    addNotification(notif);
  }

  // --- Phase 14: Android Background Scheduling & Lifecycle Simulation ---
  final List<StudyNotification> _scheduledQueue = [];
  List<StudyNotification> get scheduledQueue => List.unmodifiable(_scheduledQueue);

  void scheduleStudyKickoff({
    required DateTime time,
    required String topic,
  }) {
    final notif = StudyNotification(
      id: 'sched-kickoff-${DateTime.now().millisecondsSinceEpoch}',
      title: 'Study Session Kickoff 🚀',
      message: 'Time for your scheduled study session on $topic. Keep your momentum going!',
      category: 'session_kickoff',
      actionRoute: '/teaching',
      createdAt: time,
      priority: 'high',
    );
    _scheduledQueue.add(notif);
    notifyListeners();
  }

  void scheduleRevisionReminder({
    required DateTime time,
    required int count,
    required String subject,
  }) {
    final notif = StudyNotification(
      id: 'sched-rev-${DateTime.now().millisecondsSinceEpoch}',
      title: 'Spaced Repetition Due ⏰',
      message: '$count review items are due in $subject for memory consolidation.',
      category: 'revision_due',
      actionRoute: '/revision',
      createdAt: time,
      priority: 'medium',
    );
    _scheduledQueue.add(notif);
    notifyListeners();
  }

  void scheduleExamCountdown({
    required DateTime examDate,
    required String subject,
    required int daysRemaining,
  }) {
    final notif = StudyNotification(
      id: 'sched-exam-${DateTime.now().millisecondsSinceEpoch}',
      title: 'Exam Countdown Alert 🎯',
      message: '$subject exam is in $daysRemaining days! Autonomous agent has prioritized high-yield topics.',
      category: 'exam_alert',
      actionRoute: '/exam',
      createdAt: examDate,
      priority: 'urgent',
    );
    _scheduledQueue.add(notif);
    notifyListeners();
  }

  void scheduleAgentRecommendation({
    required String recommendation,
    required String topic,
  }) {
    final notif = StudyNotification(
      id: 'sched-agent-${DateTime.now().millisecondsSinceEpoch}',
      title: 'Agent Recommendation 💡',
      message: 'Based on your recent mastery in $topic: $recommendation',
      category: 'session_kickoff',
      actionRoute: '/agent',
      priority: 'high',
    );
    _scheduledQueue.add(notif);
    addNotification(notif);
  }

  /// Triggered when Android OS pauses or backgrounds the app
  void handleAppBackgrounded() {
    debugPrint('[NotificationService] App backgrounded. Alarms primed: ${_scheduledQueue.length}');
  }

  /// Triggered when Android OS resumes the app (surfaces pending due alarms)
  void handleAppResumed() {
    final now = DateTime.now();
    final due = _scheduledQueue.where((n) => n.createdAt.isBefore(now)).toList();
    for (final notif in due) {
      addNotification(notif);
      _scheduledQueue.remove(notif);
    }
  }

  /// Triggered after Android device reboot (re-primes scheduled notifications)
  void handleDeviceReboot() {
    debugPrint('[NotificationService] Boot completed. Re-registering background alarms.');
    notifyListeners();
  }

  /// Triggered on network connectivity transitions
  void handleNetworkStateChange(bool isConnected) {
    if (!isConnected) {
      addNotification(
        StudyNotification(
          id: 'net-offline-${DateTime.now().millisecondsSinceEpoch}',
          title: 'Offline Mode Active 🟢',
          message: 'Running 100% on local offline AI models and device storage.',
          category: 'system',
          priority: 'low',
        ),
      );
    }
  }
}
