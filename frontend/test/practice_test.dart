import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/practice/models/practice_model.dart';
import 'package:frontend/features/practice/services/practice_api_service.dart';
import 'package:frontend/features/dashboard/screens/practice_tab.dart';
import 'package:frontend/features/practice/screens/interactive_quiz_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 5 Practice & Assessment Models and Service Tests', () {
    test('QuestionModel and QuizSessionModel serialize correctly', () {
      final q = QuestionModel(
        id: 'q-101',
        orderIndex: 1,
        questionType: 'mcq',
        prompt: 'Which condition is NOT required for deadlock?',
        options: ['Mutual Exclusion', 'Hold and Wait', 'Preemption Allowed', 'Circular Wait'],
        difficulty: 'beginner',
        learningObjective: 'Recall Coffman conditions.',
        conceptTag: 'coffman_conditions',
      );

      expect(q.prompt, contains('NOT required'));
      expect(q.options.length, equals(4));

      final session = QuizSessionModel(
        sessionId: 'qs-101',
        title: 'Deadlocks Quiz',
        topic: 'Deadlocks',
        totalQuestions: 5,
        currentQuestion: q,
      );

      expect(session.sessionId, equals('qs-101'));
      expect(session.currentQuestion?.id, equals('q-101'));
    });

    test('PracticeApiService starts session and returns evaluation feedback', () async {
      final api = PracticeApiService();

      // Start session
      final session = await api.startSession(topic: 'Deadlocks');
      expect(session.sessionId, isNotEmpty);
      expect(session.currentQuestion, isNotNull);

      // Submit correct answer
      final correctRes = await api.submitAnswer(
        sessionId: session.sessionId,
        questionId: session.currentQuestion!.id,
        studentResponse: 'Preemption Allowed',
      );
      expect(correctRes.evaluation.isCorrect, isTrue);
      expect(correctRes.sessionScorePercentage, equals(100.0));

      // Submit incorrect answer (misconception)
      final wrongRes = await api.submitAnswer(
        sessionId: session.sessionId,
        questionId: session.currentQuestion!.id,
        studentResponse: 'Mutual Exclusion',
      );
      expect(wrongRes.evaluation.isCorrect, isFalse);
      expect(wrongRes.evaluation.misconceptionIdentified, isNotNull);
      expect(wrongRes.evaluation.remediationAdvice, contains('Socratic AI Teacher'));
    });
  });

  group('Phase 5 PracticeTab and InteractiveQuizScreen Widget Tests', () {
    testWidgets('PracticeTab renders topic selector, modes, weak areas, and history', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: PracticeTab(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Header
      expect(find.text('Practice & Mastery Engine'), findsOneWidget);
      expect(find.textContaining('Evidence-based testing'), findsOneWidget);

      // Verify Topic Chips
      expect(find.text('Deadlocks & Banker\'s Algorithm'), findsWidgets);
      expect(find.text('Process Synchronization'), findsWidgets);

      // Verify Options
      expect(find.text('Adaptive Concept Quiz'), findsOneWidget);
      expect(find.text('Deep Scenario & Mock Exam'), findsOneWidget);

      // Verify Weak Areas Section
      expect(find.text('Diagnosed Weak Areas & Misconceptions'), findsOneWidget);
      expect(find.textContaining('Circular Wait vs Resource Ordering'), findsOneWidget);
      expect(find.text('Re-teach with AI Teacher'), findsWidgets);

      // Verify Recent Quiz Performance
      expect(find.text('Recent Quiz Performance'), findsOneWidget);
    });

    testWidgets('InteractiveQuizScreen displays question, accepts answer, and displays misconception feedback', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: InteractiveQuizScreen(
            topic: 'Deadlocks',
            count: 2,
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Question Prompt
      expect(find.textContaining('Coffman conditions'), findsOneWidget);

      // Select Option 'Mutual Exclusion'
      final optionTile = find.text('Mutual Exclusion');
      expect(optionTile, findsOneWidget);
      await tester.tap(optionTile);
      await tester.pumpAndSettle();

      // Submit Answer
      final submitButton = find.text('Submit Answer');
      expect(submitButton, findsOneWidget);
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Verify Evaluation Feedback & Misconception Card
      expect(find.text('Incorrect / Needs Review'), findsOneWidget);
      expect(find.textContaining('Misconception:'), findsOneWidget);
      expect(find.text('Re-teach with AI Teacher'), findsOneWidget);
    });
  });
}
