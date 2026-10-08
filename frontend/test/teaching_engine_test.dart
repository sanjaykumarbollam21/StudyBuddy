import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/teaching/models/teaching_model.dart';
import 'package:frontend/features/teaching/services/teaching_api_service.dart';
import 'package:frontend/features/teaching/screens/interactive_teacher_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Phase 4A Teaching Models & Service Tests', () {
    test('TeachingEvaluationModel and TeachingTurnModel serialize correctly', () {
      final eval = TeachingEvaluationModel(
        verdict: 'correct',
        feedback: 'Exactly. You identified the key idea: circular waiting.',
        isCorrect: true,
      );

      expect(eval.isCorrect, isTrue);
      expect(eval.verdict, equals('correct'));

      final jsonEval = eval.toJson();
      final reconEval = TeachingEvaluationModel.fromJson(jsonEval);
      expect(reconEval.feedback, contains('circular waiting'));

      final turn = TeachingTurnModel(
        sessionId: 'session-123',
        state: 'check_understanding',
        teacherMessage: 'Two people holding keys waiting for each other.',
        conceptTitle: 'Deadlock Definition',
        explanation: 'Processes blocked waiting for resources.',
        analogy: 'Two people holding keys.',
        checkQuestion: 'Why can neither proceed?',
        evaluation: eval,
        masteryPercentage: 35.0,
        currentStepNumber: 1,
        totalSteps: 3,
        suggestedActions: ['Give me a hint'],
      );

      expect(turn.currentStepNumber, equals(1));
      expect(turn.masteryPercentage, equals(35.0));
      expect(turn.evaluation?.isCorrect, isTrue);
    });

    test('TeachingApiService offline simulation handles assess -> teach -> misconception -> advance', () async {
      final service = TeachingApiService();

      // 1. Start session
      final start = await service.startSession(topic: 'Deadlocks');
      expect(start.sessionId, isNotEmpty);
      expect(start.teacherMessage, contains('what do you already know'));

      // 2. Share initial intuition
      final turn1 = await service.submitStudentTurn(
        sessionId: start.sessionId,
        answer: 'I think it happens when a process gets stuck.',
      );
      expect(turn1.checkQuestion, isNotEmpty);
      expect(turn1.conceptTitle, contains('Deadlock'));

      // 3. Submit misconception
      final remed = await service.submitStudentTurn(
        sessionId: start.sessionId,
        answer: 'Deadlock happens because the CPU is too slow.',
      );
      expect(remed.evaluation?.isCorrect, isFalse);
      expect(remed.state, equals('reteaching'));
      expect(remed.teacherMessage, contains('performance'));
      expect(remed.teacherMessage, contains('simplify it'));

      // 4. Submit correct response
      final advance = await service.submitStudentTurn(
        sessionId: start.sessionId,
        answer: 'Because each one is waiting for something the other has.',
      );
      expect(advance.evaluation?.isCorrect, isTrue);
      expect(advance.currentStepNumber, equals(2));
      expect(advance.masteryPercentage, greaterThan(0.0));
    });
  });

  group('Phase 4A InteractiveTeacherScreen Widget Tests', () {
    testWidgets('InteractiveTeacherScreen renders topic, mastery, and allows student response', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: InteractiveTeacherScreen(
            topic: 'Deadlocks',
            subject: 'Operating Systems',
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Screen Header
      expect(find.text('Deadlocks'), findsOneWidget);
      expect(find.text('Operating Systems'), findsOneWidget);
      expect(find.textContaining('Mastery:'), findsOneWidget);

      // Verify Initial Teacher Probe
      expect(find.textContaining('what do you already know about Deadlocks'), findsOneWidget);

      // Verify Quick Action Pills are available
      expect(find.text('I think it happens when a process gets stuck.'), findsOneWidget);

      // Tap Quick Action Pill
      await tester.tap(find.text('I think it happens when a process gets stuck.'));
      await tester.pumpAndSettle();

      // Verify Teaching Card appeared with check question
      expect(find.textContaining('Check your understanding:'), findsWidgets);

      // Enter student answer into text field
      final textField = find.byType(TextField);
      expect(textField, findsOneWidget);
      await tester.enterText(textField, 'Because each one is waiting for something the other has.');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pumpAndSettle();

      // Verify Evaluation Banner is displayed
      expect(find.textContaining('Concept Understood!'), findsOneWidget);
      expect(find.textContaining('The Four Coffman Conditions'), findsWidgets);
    });
  });
}
