import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/notifications/notification_service.dart';
import 'package:frontend/core/storage/android_local_llm_provider.dart';
import 'package:frontend/core/storage/offline_storage_service.dart';
import 'package:frontend/features/agent/models/agent_task_model.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 14: Real Android Runtime & Offline Storage Tests', () {
    test('OfflineStorageService caches and restores AgentTask, mastery, chunks, and planner', () async {
      final storage = OfflineStorageService();

      // 1. AgentTask Persistence
      final task = AgentTaskModel(
        id: 'task-android-42',
        userId: 'student-android',
        goal: 'Conquer Deadlocks before Midterm',
        reason: 'Mastery at 48% with exam in 4 days',
        priority: 'critical',
        permissionLevel: 'requires_permission',
        currentState: 'executing',
        allocatedMinutes: 60,
        currentStepIndex: 2,
        isResumable: true,
        proposedActions: [
          AgentActionStepModel(
            step: 1,
            type: 'reteach',
            topic: 'Deadlocks',
            durationMins: 25,
            engine: 'TeacherEngine',
            description: 'Socratic review',
          ),
          AgentActionStepModel(
            step: 2,
            type: 'practice',
            topic: 'Deadlocks',
            durationMins: 20,
            engine: 'PracticeEngine',
            description: 'Diagnostic questions',
          ),
        ],
      );

      await storage.saveActiveAgentTask(task);
      final loadedTask = await storage.loadActiveAgentTask();
      expect(loadedTask, isNotNull);
      expect(loadedTask!.id, equals('task-android-42'));
      expect(loadedTask.currentStepIndex, equals(2));
      expect(loadedTask.isResumable, isTrue);

      // 2. Mastery Persistence
      await storage.saveMastery('Deadlocks', 82.5);
      final loadedMastery = await storage.loadMastery('Deadlocks');
      expect(loadedMastery, equals(82.5));

      // 3. Revision Items Persistence
      final revisions = [
        {'id': 'rev-1', 'topic': 'Coffman Conditions', 'interval_days': 3},
        {'id': 'rev-2', 'topic': 'Banker Algorithm', 'interval_days': 6},
      ];
      await storage.saveRevisionItems(revisions);
      final loadedRevisions = await storage.loadRevisionItems();
      expect(loadedRevisions.length, equals(2));
      expect(loadedRevisions[0]['topic'], equals('Coffman Conditions'));

      // 4. Document Chunks Persistence
      final chunks = [
        {'id': 'chk-1', 'content': 'Deadlock mutual exclusion principle.'},
        {'id': 'chk-2', 'content': 'Circular wait prevention order.'},
      ];
      await storage.saveDocumentChunks('doc-os-101', chunks);
      final loadedChunks = await storage.loadDocumentChunks('doc-os-101');
      expect(loadedChunks.length, equals(2));

      // 5. Planner Schedule Persistence
      final schedule = {
        'subject': 'Operating Systems',
        'target_date': '2026-10-15',
        'sessions_count': 6,
      };
      await storage.savePlannerSchedule(schedule);
      final loadedSchedule = await storage.loadPlannerSchedule();
      expect(loadedSchedule!['subject'], equals('Operating Systems'));
    });

    test('AndroidLocalLLMProvider executes on-device Socratic teaching and diagnostic evaluation', () async {
      final provider = AndroidLocalLLMProvider();
      expect(provider.providerName, equals('android_on_device_socratic'));

      // 1. Socratic Teaching with Document Grounding
      final socraticPrompt = await provider.generateSocraticResponse(
        prompt: 'Explain deadlocks',
        conceptTitle: 'Deadlocks',
        documentContext: 'Syllabus Chapter 7: Deadlocks',
      );
      expect(socraticPrompt, contains('four Coffman conditions'));
      expect(socraticPrompt, contains('Circular Wait'));

      // 2. Diagnostic: Correct answer
      final correctEval = await provider.evaluateAnswer(
        question: 'What causes deadlock?',
        studentAnswer: 'Circular wait and mutual exclusion',
        expectedConcept: 'Coffman conditions',
      );
      expect(correctEval['verdict'], equals('correct'));
      expect(correctEval['is_correct'], isTrue);

      // 3. Diagnostic: Misconception answer (CPU speed)
      final miscEval = await provider.evaluateAnswer(
        question: 'What causes deadlock?',
        studentAnswer: 'The CPU is too slow',
        expectedConcept: 'Coffman conditions',
      );
      expect(miscEval['verdict'], equals('misconception'));
      expect(miscEval['is_correct'], isFalse);
      expect(miscEval['misconception_identified'], contains('Performance vs Resource Ownership'));

      // 4. Diagnostic: Struggling student
      final struggleEval = await provider.evaluateAnswer(
        question: 'What is circular wait?',
        studentAnswer: 'I do not know, please help me',
        expectedConcept: 'Closed loop dependency',
      );
      expect(struggleEval['verdict'], equals('struggling'));
    });

    test('NotificationService manages Android background scheduling, reboot re-registration, and lifecycle', () {
      final notifService = NotificationService();

      // 1. Schedule background alarms
      final kickoffTime = DateTime.now().add(const Duration(hours: 2));
      notifService.scheduleStudyKickoff(time: kickoffTime, topic: 'Deadlocks & Banker Algorithm');
      expect(notifService.scheduledQueue.any((n) => n.category == 'session_kickoff'), isTrue);

      final revisionTime = DateTime.now().add(const Duration(hours: 4));
      notifService.scheduleRevisionReminder(time: revisionTime, count: 5, subject: 'Operating Systems');
      expect(notifService.scheduledQueue.any((n) => n.category == 'revision_due'), isTrue);

      final examDate = DateTime.now().add(const Duration(days: 4));
      notifService.scheduleExamCountdown(examDate: examDate, subject: 'Operating Systems', daysRemaining: 4);
      expect(notifService.scheduledQueue.any((n) => n.category == 'exam_alert'), isTrue);

      // Agent recommendation
      notifService.scheduleAgentRecommendation(
        recommendation: 'Spend 20 mins on Circular Wait resource ordering',
        topic: 'Deadlocks',
      );
      expect(notifService.notifications.any((n) => n.title.contains('Agent Recommendation')), isTrue);

      // 2. Android Lifecycle: Background & Resume
      notifService.handleAppBackgrounded();
      notifService.handleAppResumed();

      // 3. Android Lifecycle: Reboot
      notifService.handleDeviceReboot();

      // 4. Android Lifecycle: Network State Change (Offline mode banner)
      notifService.handleNetworkStateChange(false);
      expect(notifService.notifications.any((n) => n.title.contains('Offline Mode Active')), isTrue);
    });
  });
}
