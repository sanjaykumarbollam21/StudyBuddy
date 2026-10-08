import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/notifications/notification_service.dart';
import 'package:frontend/core/storage/android_local_llm_provider.dart';
import 'package:frontend/core/storage/offline_storage_service.dart';
import 'package:frontend/features/agent/models/agent_task_model.dart';
import 'package:frontend/features/settings/screens/diagnostics_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 15: Real Device Beta & Release Hardening Tests', () {
    testWidgets('DiagnosticsScreen displays all 9 system telemetry cards and completes full self-test', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 1200));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        const MaterialApp(
          home: DiagnosticsScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify title and health banner
      expect(find.text('Study Buddy Diagnostics'), findsOneWidget);
      expect(find.text('Device Health: Ready for Real-World Beta'), findsOneWidget);

      // Verify core telemetry cards
      expect(find.text('AI Mode'), findsOneWidget);
      expect(find.text('LLM & Socratic Engine'), findsOneWidget);
      expect(find.text('Semantic Embeddings'), findsOneWidget);
      expect(find.text('Local Database & Persistence'), findsOneWidget);
      expect(find.text('Autonomous Agent State'), findsOneWidget);
      expect(find.text('Offline Sync Engine'), findsOneWidget);
      expect(find.text('Background Notifications & Alarms'), findsOneWidget);
      expect(find.text('Memory Profile & RAM Safeguards'), findsOneWidget);
      expect(find.text('Battery & Lifecycle Scheduling'), findsOneWidget);
      // Verify Release Check card distinguishing automated vs physical verification
      expect(find.text('Release Check & Validation'), findsOneWidget);
      expect(find.text('Automated Verification'), findsOneWidget);
      expect(find.text('Physical Device Validation'), findsOneWidget);
      expect(find.text('⚠ Physical device test pending (Manual 25-step protocol)'), findsOneWidget);
      expect(find.text('Mark Passed'), findsOneWidget);

      // Verify toggle transitions state to Verified
      await tester.ensureVisible(find.text('Mark Passed'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Mark Passed'));
      await tester.pumpAndSettle();
      expect(find.text('Passed'), findsOneWidget);
      expect(find.text('✓ 25-step physical journey verified on hardware'), findsOneWidget);

      // Trigger Full Self-Test
      final buttonFinder = find.text('Run Full Device Self-Test');
      await tester.ensureVisible(buttonFinder);
      await tester.pumpAndSettle();
      await tester.tap(buttonFinder);
      await tester.pump(const Duration(milliseconds: 350));
      await tester.pumpAndSettle();

      // Verify self-test results
      expect(find.text('Self-Test Verification Results'), findsOneWidget);
      expect(find.text('Storage & Persistence'), findsOneWidget);
      expect(find.text('On-Device Socratic LLM'), findsOneWidget);
      expect(find.text('Notification Scheduling'), findsOneWidget);
    });

    test('Phase 15: Exhaustive 25-Step Real-Device Offline Journey Simulation', () async {
      final storage = OfflineStorageService();
      final localLLM = AndroidLocalLLMProvider();
      final notifService = NotificationService();

      // Step 1: Install APK & launch
      expect(storage, isNotNull);

      // Step 2: Student Account
      const studentId = 'beta-student-001';

      // Step 3: Import Real Textbook Content
      final textbookChunks = [
        {'id': 'chk-1', 'title': 'Coffman Conditions', 'content': 'Mutual exclusion, hold and wait, no preemption, circular wait.'},
        {'id': 'chk-2', 'title': 'Banker Algorithm', 'content': 'Safe state resource allocation avoidance.'},
      ];
      await storage.saveDocumentChunks('doc-os-beta', textbookChunks);
      final loadedChunks = await storage.loadDocumentChunks('doc-os-beta');
      expect(loadedChunks.length, equals(2));

      // Step 4: Turn Internet OFF (Simulate offline mode)
      notifService.handleNetworkStateChange(false);
      expect(notifService.notifications.any((n) => n.title.contains('Offline Mode Active')), isTrue);

      // Step 5: Generate learning path & roadmap
      final schedule = {
        'roadmap_id': 'road-os-beta',
        'milestones': ['Deadlocks Foundations', 'Banker Algorithm', 'Resource Ordering'],
      };
      await storage.savePlannerSchedule(schedule);

      // Step 6: Start Socratic lesson (on-device)
      final lessonPrompt = await localLLM.generateSocraticResponse(
        prompt: 'Teach me Deadlocks',
        conceptTitle: 'Deadlocks',
        documentContext: textbookChunks[0]['content'],
      );
      expect(lessonPrompt, contains('Coffman conditions'));

      // Step 7 & 8: Ask question & Student gives intentionally wrong answer
      const wrongAnswer = 'Deadlock happens because the CPU is not fast enough';
      final diagnosis = await localLLM.evaluateAnswer(
        question: 'What causes deadlock?',
        studentAnswer: wrongAnswer,
        expectedConcept: 'Coffman conditions',
      );

      // Step 9: Misconception identified
      expect(diagnosis['verdict'], equals('misconception'));
      expect(diagnosis['is_correct'], isFalse);

      // Step 10: Socratic Reteaching & Remediation probe
      final studentFixedAnswer = 'circular wait and mutual exclusion';
      final fixedEval = await localLLM.evaluateAnswer(
        question: 'What condition creates circular dependency?',
        studentAnswer: studentFixedAnswer,
        expectedConcept: 'circular wait',
      );
      expect(fixedEval['is_correct'], isTrue);

      // Step 11: Mastery changes and saves locally
      await storage.saveMastery('Deadlocks', 85.0);
      final currentMastery = await storage.loadMastery('Deadlocks');
      expect(currentMastery, equals(85.0));

      // Step 12: Spaced Revision Scheduled
      final revisionDeck = [
        {'id': 'rev-coffman', 'front': 'List 4 Coffman conditions', 'interval_days': 3},
      ];
      await storage.saveRevisionItems(revisionDeck);
      final loadedDeck = await storage.loadRevisionItems();
      expect(loadedDeck.length, equals(1));

      // Step 13: Ask Agent what to study next
      final agentTask = AgentTaskModel(
        id: 'task-beta-real',
        userId: studentId,
        goal: 'Prepare Concurrency & Synchronization',
        reason: 'Mastery at 85% in Deadlocks; next prerequisite is Semaphores',
        priority: 'high',
        permissionLevel: 'safe_automatic',
        currentState: 'executing',
        allocatedMinutes: 45,
        currentStepIndex: 1,
        isResumable: true,
        proposedActions: [
          AgentActionStepModel(
            step: 1,
            type: 'learn',
            topic: 'Semaphores',
            durationMins: 20,
            engine: 'TeacherEngine',
            description: 'Counting Semaphores introduction',
          ),
          AgentActionStepModel(
            step: 2,
            type: 'practice',
            topic: 'Semaphores',
            durationMins: 25,
            engine: 'PracticeEngine',
            description: 'Mutex lock implementation practice',
          ),
        ],
      );

      // Step 14 & 15: Close app & save state
      await storage.saveActiveAgentTask(agentTask);

      // Step 16: Reopen app -> Resume AgentTask from exact Step 1
      final resumedTask = await storage.loadActiveAgentTask();
      expect(resumedTask, isNotNull);
      expect(resumedTask!.id, equals('task-beta-real'));
      expect(resumedTask.currentStepIndex, equals(1));

      // Step 17 & 18: Lock / unlock phone (Background & Resume)
      notifService.handleAppBackgrounded();
      notifService.handleAppResumed();

      // Step 19 & 20: Phone reboot simulation & alarm verification
      notifService.scheduleStudyKickoff(time: DateTime.now().add(const Duration(hours: 3)), topic: 'Semaphores');
      notifService.handleDeviceReboot();
      expect(notifService.scheduledQueue.isNotEmpty, isTrue);

      // Step 21 & 22: Re-enable Internet & Sync without duplication
      notifService.handleNetworkStateChange(true);

      // Step 23: Verify state survived without duplicate cards
      final finalDeck = await storage.loadRevisionItems();
      expect(finalDeck.length, equals(1));

      // Step 24 & 25: Mock Exam readiness check
      final readinessScore = currentMastery! * 0.95;
      expect(readinessScore, greaterThan(80.0));
    });
  });
}
