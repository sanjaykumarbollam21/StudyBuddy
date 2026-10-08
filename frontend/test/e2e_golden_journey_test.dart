import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/sync/sync_service.dart';
import 'package:frontend/core/notifications/notification_service.dart';
import 'package:frontend/features/auth/controllers/auth_controller.dart';
import 'package:frontend/features/dashboard/screens/main_shell_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AuthController authController;

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    authController = AuthController();
    await authController.initialize();
    await authController.loginWithDemoAccount();
  });

  group('Phase 11: End-to-End Golden Journey Product Validation', () {
    testWidgets('Complete Golden Journey: Auth -> Shell -> Notifications -> AI Mode -> Offline Sync', (tester) async {
      tester.view.physicalSize = const Size(1200, 1600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      // Step 1: Launch Main Shell Screen with Authenticated Student
      await tester.pumpWidget(
        MaterialApp(
          home: MainShellScreen(authController: authController),
        ),
      );
      await tester.pumpAndSettle();

      // Verify app bar title and student identity
      expect(find.text('Study Buddy'), findsOneWidget);
      expect(find.text('S'), findsOneWidget); // Sanjay's avatar initial

      // Step 2: Proactive Notifications Verification
      final notifService = NotificationService();
      expect(notifService.notifications.length, greaterThanOrEqualTo(3));

      // Open Notifications sheet
      final notifButton = find.byTooltip('Notifications');
      expect(notifButton, findsOneWidget);
      await tester.tap(notifButton);
      await tester.pumpAndSettle();

      // Verify Proactive alerts (Session kickoff, revision due, exam countdown)
      expect(find.text('Notifications & Reminders'), findsOneWidget);
      expect(find.textContaining('Study Session Kickoff'), findsOneWidget);
      expect(find.textContaining('Spaced Revision Due'), findsOneWidget);

      // Dismiss bottom sheet
      Navigator.of(tester.element(find.text('Notifications & Reminders'))).pop();
      await tester.pumpAndSettle();

      // Step 3: AI Mode & Offline Sync Screen Navigation
      final settingsButton = find.byTooltip('AI Mode & Offline Sync');
      expect(settingsButton, findsOneWidget);
      await tester.tap(settingsButton);
      await tester.pumpAndSettle();

      // Verify AI Provider Configurations
      expect(find.text('AI Mode & Offline Sync'), findsOneWidget);
      expect(find.text('🟢 Offline AI — No Internet required'), findsOneWidget);
      expect(find.text('Local Embedding Model'), findsOneWidget);
      expect(find.text('BAAI/bge-small-en-v1.5 (384 dims, ONNX)'), findsOneWidget);

      // Switch to Online AI
      await tester.ensureVisible(find.text('Online AI'));
      await tester.tap(find.text('Online AI'));
      await tester.pumpAndSettle();

      expect(find.text('🔵 Online — Cloud AI enabled'), findsOneWidget);

      // Step 4: Offline Simulation & Recovery
      final syncService = SyncService();
      syncService.clearQueue();

      // Student studies offline: records mastery & revision changes
      syncService.recordChange(
        entityType: 'mastery',
        entityId: 'topic-deadlock-avoidance',
        action: 'update',
        payload: {
          'topic_id': 'topic-deadlock-avoidance',
          'mastery_percentage': 92.5,
          'times_practiced': 7,
          'weak_areas': [],
        },
      );
      syncService.recordChange(
        entityType: 'study_plan_item',
        entityId: 'plan-item-e2e-01',
        action: 'complete',
        payload: {
          'status': 'completed',
          'performance_score': 0.95,
        },
      );

      expect(syncService.pendingCount, equals(2));

      // Student comes back online: triggers sync
      await tester.ensureVisible(find.text('Sync Now'));
      await tester.tap(find.text('Sync Now'));
      await tester.pumpAndSettle();

      // Changes synced & queue emptied
      expect(syncService.pendingCount, equals(0));
      expect(syncService.lastSyncedAt, isNotNull);
      expect(find.textContaining('Sync completed'), findsOneWidget);
    });

    test('Offline Failure Recovery: Disconnect -> Buffer -> Reconnect -> Idempotent Sync', () async {
      final syncService = SyncService();
      syncService.clearQueue();

      // Simulate network disconnection: 3 learning actions queued
      syncService.recordChange(
        entityType: 'mastery',
        entityId: 'topic-paging',
        action: 'update',
        payload: {'mastery_percentage': 78.0},
      );
      syncService.recordChange(
        entityType: 'revision_item',
        entityId: 'rev-item-e2e-99',
        action: 'update',
        payload: {'ease_factor': 2.6, 'repetition_interval_days': 8},
      );
      syncService.recordChange(
        entityType: 'study_plan_item',
        entityId: 'plan-item-e2e-02',
        action: 'complete',
        payload: {'status': 'completed'},
      );

      expect(syncService.pendingCount, equals(3));

      // Network restored: sync succeeds
      final success = await syncService.synchronize(client: null);
      expect(success, isTrue);
      expect(syncService.pendingCount, equals(0));
      expect(syncService.lastSyncedAt, isNotNull);

      // Second sync should be idempotent and succeed without pending items
      final secondSync = await syncService.synchronize(client: null);
      expect(secondSync, isTrue);
      expect(syncService.pendingCount, equals(0));
    });

    test('Data Integrity: SyncChangeItem serialization retains complex payloads', () {
      final item = SyncChangeItem(
        id: 'sync-item-integrity-01',
        entityType: 'mastery',
        entityId: 'topic-concurrency-locks',
        action: 'update',
        clientTimestamp: DateTime.parse('2026-10-07T12:00:00.000Z'),
        payload: {
          'mastery_percentage': 88.5,
          'weak_areas': ['Peterson Algorithm', 'Test-and-Set'],
          'difficulty': 'hard',
          'metrics': {'retention': 0.92, 'attempts': 12},
        },
        version: 2,
      );

      final jsonMap = item.toJson();
      final restored = SyncChangeItem.fromJson(jsonMap);

      expect(restored.id, equals('sync-item-integrity-01'));
      expect(restored.entityType, equals('mastery'));
      expect(restored.version, equals(2));
      expect(restored.payload['mastery_percentage'], equals(88.5));
      expect(restored.payload['weak_areas'].length, equals(2));
      expect(restored.payload['metrics']['retention'], equals(0.92));
    });
  });
}
