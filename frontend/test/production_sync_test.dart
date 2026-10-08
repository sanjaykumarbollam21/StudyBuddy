import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/sync/sync_service.dart';
import 'package:frontend/core/notifications/notification_service.dart';
import 'package:frontend/features/settings/screens/ai_settings_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 10: SyncService & Offline Persistence Tests', () {
    test('Enqueue offline change items and record changes', () {
      final syncService = SyncService();
      syncService.clearQueue();
      expect(syncService.pendingCount, equals(0));

      syncService.recordChange(
        entityType: 'mastery',
        entityId: 'topic-sync-01',
        action: 'update',
        payload: {'mastery_percentage': 85.0, 'times_practiced': 4},
      );

      syncService.recordChange(
        entityType: 'revision_item',
        entityId: 'rev-01',
        action: 'update',
        payload: {'ease_factor': 2.5, 'repetition_interval_days': 5},
      );

      expect(syncService.pendingCount, equals(2));
      final first = syncService.pendingQueue.first;
      expect(first.entityType, equals('mastery'));
      expect(first.payload['mastery_percentage'], equals(85.0));

      // Test serialization
      final jsonMap = first.toJson();
      final parsed = SyncChangeItem.fromJson(jsonMap);
      expect(parsed.entityId, equals('topic-sync-01'));
    });

    test('Offline local simulation sync clears queue and sets lastSyncedAt', () async {
      final syncService = SyncService();
      syncService.clearQueue();
      syncService.recordChange(
        entityType: 'study_plan_item',
        entityId: 'plan-item-99',
        action: 'update',
        payload: {'status': 'completed'},
      );
      expect(syncService.pendingCount, equals(1));

      final success = await syncService.synchronize(client: null);
      expect(success, isTrue);
      expect(syncService.pendingCount, equals(0));
      expect(syncService.lastSyncedAt, isNotNull);
    });
  });

  group('Phase 10: NotificationService Tests', () {
    test('Default proactive study notifications and mark as read', () {
      final notifService = NotificationService();
      expect(notifService.notifications.length, greaterThanOrEqualTo(3));

      final unreadBefore = notifService.unreadCount;
      expect(unreadBefore, greaterThan(0));

      final first = notifService.notifications.first;
      notifService.markAsRead(first.id);
      expect(first.isRead, isTrue);
      expect(notifService.unreadCount, equals(unreadBefore - 1));

      // Mark all read
      notifService.markAllAsRead();
      expect(notifService.unreadCount, equals(0));
    });

    test('Generate proactive exam countdown alert', () {
      final notifService = NotificationService();
      final initialCount = notifService.notifications.length;

      notifService.generateProactiveAlert(
        title: 'Exam Alert ⚠️',
        message: 'Your OS exam is 3 days away. Concurrency is below target mastery.',
        category: 'exam_alert',
        actionRoute: '/exam',
        priority: 'urgent',
      );

      expect(notifService.notifications.length, equals(initialCount + 1));
      final newest = notifService.notifications.first;
      expect(newest.category, equals('exam_alert'));
      expect(newest.priority, equals('urgent'));
      expect(newest.isRead, isFalse);
    });
  });

  group('Phase 10: AISettingsScreen Widget Tests', () {
    testWidgets('Renders AI provider mode options and switches to Hybrid AI', (tester) async {
      tester.view.physicalSize = const Size(1200, 1600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        const MaterialApp(
          home: AISettingsScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Screen Header and Default Mode
      expect(find.text('AI Mode & Offline Sync'), findsOneWidget);
      expect(find.text('🟢 Offline AI — No Internet required'), findsOneWidget);
      expect(find.text('Offline AI'), findsOneWidget);
      expect(find.text('Hybrid AI'), findsOneWidget);
      expect(find.text('Online AI'), findsOneWidget);

      // Verify Local model details
      expect(find.text('BAAI/bge-small-en-v1.5 (384 dims, ONNX)'), findsOneWidget);

      // Select Hybrid AI mode
      await tester.ensureVisible(find.text('Hybrid AI'));
      await tester.tap(find.text('Hybrid AI'));
      await tester.pumpAndSettle();

      // Check indicator badge updated
      expect(find.text('🟡 Hybrid — Local data + cloud reasoning'), findsOneWidget);

      // Verify sync button is visible
      await tester.ensureVisible(find.text('Sync Now'));
      expect(find.text('Sync Now'), findsOneWidget);
      await tester.tap(find.text('Sync Now'));
      await tester.pumpAndSettle();

      // Verify successful sync snackbar or message
      expect(find.textContaining('Sync completed'), findsOneWidget);
    });
  });
}
