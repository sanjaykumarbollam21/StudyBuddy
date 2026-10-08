import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/agent/models/agent_task_model.dart';
import 'package:frontend/features/agent/screens/autonomous_agent_screen.dart';
import 'package:frontend/features/settings/screens/ai_settings_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 13: Production Integration & Real-World AI Tests', () {
    test('AgentTaskModel persistent resumability fields serialization', () {
      final now = DateTime.now();
      final task = AgentTaskModel(
        id: 'task-persisted-1',
        userId: 'student-42',
        goal: 'Prepare Deadlocks for Midterm',
        reason: 'Mastery at 48% with exam approaching',
        priority: 'critical',
        permissionLevel: 'requires_permission',
        currentState: 'paused',
        allocatedMinutes: 60,
        currentStepIndex: 2,
        isResumable: true,
        stepProgress: {
          '1': {'status': 'completed', 'engine': 'TeacherEngine'},
          '2': {'status': 'completed', 'engine': 'PracticeEngine'},
        },
        interruptedAt: now,
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
            description: 'Targeted quiz',
          ),
        ],
      );

      final json = task.toJson();
      expect(json['current_step_index'], equals(2));
      expect(json['is_resumable'], isTrue);
      expect(json['current_state'], equals('paused'));
      expect(json['step_progress']['1']['status'], equals('completed'));

      final restored = AgentTaskModel.fromJson(json);
      expect(restored.currentStepIndex, equals(2));
      expect(restored.isResumable, isTrue);
      expect(restored.currentState, equals('paused'));
      expect(restored.stepProgress['2']['engine'], equals('PracticeEngine'));
      expect(restored.interruptedAt, isNotNull);
    });

    testWidgets('AutonomousAgentScreen renders task orchestration and executes cleanly', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 1000));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        const MaterialApp(
          home: AutonomousAgentScreen(),
        ),
      );

      await tester.pumpAndSettle();

      // Header and Active Orchestrator badge
      expect(find.text('Autonomous Study Agent'), findsOneWidget);
      expect(find.text('Active Orchestrator'), findsOneWidget);

      // Actions section
      expect(find.text('Orchestrated Actions:'), findsOneWidget);
      expect(find.text('Start Autonomous Session'), findsOneWidget);

      // Trigger session start
      await tester.tap(find.text('Start Autonomous Session'));
      await tester.pumpAndSettle();

      // Session completed state
      expect(find.text('Session Completed'), findsOneWidget);
    });

    testWidgets('AISettingsScreen displays Ollama local LLM settings and 16GB RAM memory profile', (tester) async {
      await tester.binding.setSurfaceSize(const Size(1200, 1000));
      addTearDown(() => tester.binding.setSurfaceSize(null));

      await tester.pumpWidget(
        const MaterialApp(
          home: AISettingsScreen(),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('AI Mode & Offline Sync'), findsOneWidget);
      expect(find.text('Offline Local LLM (Ollama)'), findsOneWidget);
      expect(find.textContaining('16GB RAM Profile'), findsOneWidget);
      expect(find.text('Local Embedding Model'), findsOneWidget);
      expect(find.text('Offline-First Synchronization'), findsOneWidget);
    });
  });
}
