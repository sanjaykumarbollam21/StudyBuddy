import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/agent/models/agent_task_model.dart';
import 'package:frontend/features/agent/services/agent_api_service.dart';
import 'package:frontend/features/agent/screens/autonomous_agent_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 12: Autonomous Study Agent Model & Service Tests', () {
    test('AgentTaskModel serialization and deserialization retains step details', () {
      final step = AgentActionStepModel(
        step: 1,
        type: 'reteach',
        topic: 'Deadlocks',
        durationMins: 25,
        engine: 'TeacherEngine',
        description: 'Socratic reteaching on Banker Algorithm',
      );

      final task = AgentTaskModel(
        id: 'task-test-01',
        userId: 'usr-101',
        goal: 'Repair Deadlocks gap',
        reason: 'Mastery at 48% with exam in 5 days',
        priority: 'critical',
        permissionLevel: 'requires_permission',
        currentState: 'proposed',
        allocatedMinutes: 60,
        proposedActions: [step],
        explanationBreakdown: {'top_topic': 'Deadlocks', 'mastery': 48.0},
      );

      final json = task.toJson();
      expect(json['id'], equals('task-test-01'));
      expect(json['allocated_minutes'], equals(60));
      expect(json['proposed_actions'].length, equals(1));

      final restored = AgentTaskModel.fromJson(json);
      expect(restored.goal, equals('Repair Deadlocks gap'));
      expect(restored.proposedActions.first.engine, equals('TeacherEngine'));
      expect(restored.proposedActions.first.durationMins, equals(25));
    });

    test('AgentApiService offline evaluation and task execution returns expected flow', () async {
      final api = AgentApiService();

      final task = await api.evaluateState(availableMinutes: 60);
      expect(task.id, isNotEmpty);
      expect(task.priority, equals('critical'));
      expect(task.proposedActions.length, equals(4));

      final execRes = await api.executeTask(task.id);
      expect(execRes['success'], isTrue);
      expect(execRes['current_state'], equals('completed'));
      expect(execRes['mastery_updated']['mastery_percentage'], greaterThan(80.0));

      final chat = await api.chatWithAgent('I have one hour. Prepare me for exam.');
      expect(chat.intentDetected, equals('autonomous_exam_prep'));
      expect(chat.reply, contains('Deadlocks'));
      expect(chat.orchestratedEngines, contains('TeacherEngine'));
    });
  });

  group('Phase 12: AutonomousAgentScreen Widget Tests', () {
    testWidgets('Renders Autonomous Study Agent Screen, explains decision, and executes workflow', (tester) async {
      tester.view.physicalSize = const Size(1200, 1600);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        const MaterialApp(
          home: AutonomousAgentScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Header & Orchestrator Badge
      expect(find.text('Autonomous Study Agent'), findsOneWidget);
      expect(find.text('Active Orchestrator'), findsOneWidget);
      expect(find.text('Available Study Time:'), findsOneWidget);

      // Verify Task Recommendation Card
      expect(find.textContaining('Repair Deadlocks'), findsOneWidget);
      expect(find.text('CRITICAL'), findsOneWidget);
      expect(find.text('60 min allocated'), findsOneWidget);

      // Verify Orchestrated Engine Steps
      expect(find.text('Engine: TeacherEngine'), findsOneWidget);
      expect(find.text('Engine: PracticeEngine'), findsOneWidget);
      expect(find.text('Engine: RevisionEngine'), findsOneWidget);

      // Test "Why this?" Explainability Dialog
      final whyButton = find.text('Why this?');
      expect(whyButton, findsOneWidget);
      await tester.tap(whyButton);
      await tester.pumpAndSettle();

      expect(find.text('Why Did Study Buddy Choose This?'), findsOneWidget);
      expect(find.textContaining('Current Topic Mastery'), findsOneWidget);
      expect(find.textContaining('Exam Blueprint Importance'), findsOneWidget);

      // Dismiss dialog
      Navigator.of(tester.element(find.text('Why Did Study Buddy Choose This?'))).pop();
      await tester.pumpAndSettle();

      // Test Autonomous Execution
      final startButton = find.text('Start Autonomous Session');
      expect(startButton, findsOneWidget);
      await tester.tap(startButton);
      await tester.pumpAndSettle();

      expect(find.text('Session Completed'), findsOneWidget);
      expect(find.textContaining('Successfully executed 4 orchestrated steps'), findsOneWidget);

      // Test Quick Prompt Chip
      final chipFinder = find.text('Fix my weakest topic');
      expect(chipFinder, findsOneWidget);
      await tester.tap(chipFinder);
      await tester.pumpAndSettle();

      expect(find.textContaining('Analyzing your preparation state'), findsOneWidget);
    });
  });
}
