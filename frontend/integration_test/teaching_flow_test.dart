import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:frontend/core/errors/app_exception.dart';
import 'package:frontend/features/teaching/models/teaching_model.dart';
import 'package:frontend/features/teaching/screens/interactive_teacher_screen.dart';
import 'package:frontend/features/teaching/services/teaching_api_service.dart';

/// Deterministic in-memory fake API service modeling the Phase 4A Socratic teaching loop.
/// Eliminates network flakiness, LAN backend dependencies, and third-party LLM rate limits.
class FakeTeachingApiService extends TeachingApiService {
  bool simulateFailure = false;
  int turnCount = 0;

  @override
  Future<TeachingTurnModel> startSession({
    required String topic,
    String? subject,
    String? documentId,
    String? documentName,
    String? documentText,
    List<Map<String, dynamic>>? documentChunks,
    String? studentGoal,
  }) async {
    turnCount = 0;
    return TeachingTurnModel(
      sessionId: 'test-session-int-001',
      state: 'assess_prior_knowledge',
      teacherMessage:
          'Before we start, what do you already know about rational agents?',
      checkQuestion:
          'Before we start, what do you already know about rational agents?',
      conceptTitle: 'Rational Agents — Prior Knowledge Assessment',
      masteryPercentage: 0.0,
      currentStepNumber: 1,
      totalSteps: 3,
      suggestedActions: [
        'A rational agent acts to achieve the best expected outcome',
        'I know a little bit',
        'Just give me the basics',
      ],
    );
  }

  @override
  Future<TeachingTurnModel> submitStudentTurn({
    required String sessionId,
    required String answer,
    String actionType = 'answer',
    String? topic,
    String? documentId,
    String? documentName,
    String? documentText,
    List<Map<String, dynamic>>? documentChunks,
    int currentStepNumber = 1,
  }) async {
    if (simulateFailure) {
      throw NetworkException(
        'Connection lost. Your answer is preserved. Tap to retry.',
      );
    }

    turnCount++;

    // Turn 1: Student submits a misconception -> Teacher diagnoses and remediates
    if (answer.toLowerCase().contains('fast cpu') ||
        answer.toLowerCase().contains('cpu')) {
      return TeachingTurnModel(
        sessionId: sessionId,
        state: 'reteaching',
        teacherMessage:
            'A common misconception is thinking rationality is speed.\n\n'
            'Think of a fast race car heading in the wrong direction: raw speed does not reach the goal.\n\n'
            'Rationality means selecting actions that maximize expected performance measure given percepts.\n\n'
            '🎯 Check your understanding:\nDoes computational speed alone define a rational agent?',
        checkQuestion:
            'Does computational speed alone define a rational agent?',
        conceptTitle: 'Rationality vs Raw Performance',
        explanation:
            'Rationality is action correctness relative to a performance measure.',
        analogy:
            'A fast race car heading in the wrong direction does not reach the goal any faster.',
        evaluation: TeachingEvaluationModel(
          verdict: 'misconception',
          feedback:
              'Performance speed is not rationality. Rationality is selecting actions that maximize expected outcome.',
          misconception: 'Equating speed with rationality',
          isCorrect: false,
        ),
        masteryPercentage: 25.0,
        currentStepNumber: 1,
        totalSteps: 3,
        suggestedActions: [
          'No, selecting the best action relative to the goal is what matters',
          'Explain simpler',
          'Give me a hint',
        ],
      );
    }

    // Turn 2: Remediation answered correctly -> Advance to Step 2 (PEAS Framework)
    if (turnCount == 2) {
      return TeachingTurnModel(
        sessionId: sessionId,
        state: 'check_understanding',
        teacherMessage:
            'Spot on! Rationality is about expected success, not sheer computation speed.\n\n'
            'Now let\'s look at PEAS Framework (Performance, Environment, Actuators, Sensors):\n\n'
            'Every rational agent is designed around PEAS.\n\n'
            '🎯 Check your understanding:\nWhat does the "P" in PEAS stand for?',
        checkQuestion: 'What does the "P" in PEAS stand for?',
        conceptTitle: 'PEAS Framework',
        explanation: 'PEAS defines the agent task environment.',
        analogy: 'PEAS is the specification sheet for building an AI system.',
        evaluation: TeachingEvaluationModel(
          verdict: 'correct',
          feedback: 'Excellent reasoning!',
          isCorrect: true,
        ),
        masteryPercentage: 65.0,
        currentStepNumber: 2,
        totalSteps: 3,
        suggestedActions: [
          'Performance Measure',
          'Processing Power',
          'Program Execution',
        ],
      );
    }

    // Turn 3: Final check answered correctly -> Lesson Completed 100% Mastery
    return TeachingTurnModel(
      sessionId: sessionId,
      state: 'completed',
      teacherMessage:
          '🎓 Outstanding work! You have completely mastered the core foundations of Rational Agents & PEAS.\n\n'
          '+ Mastery: 100% Complete\n'
          '+ All Check Questions Solved',
      conceptTitle: 'Lesson Complete — 100% Mastery',
      evaluation: TeachingEvaluationModel(
        verdict: 'correct',
        feedback: 'Perfect! "P" stands for Performance Measure.',
        isCorrect: true,
      ),
      masteryPercentage: 100.0,
      currentStepNumber: 3,
      totalSteps: 3,
      isLessonCompleted: true,
      suggestedActions: [
        'Take a Practice Quiz',
        'Learn Next Topic',
        'Return to Materials',
      ],
    );
  }
}

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Socratic AI Teaching Flow Integration Tests', () {
    testWidgets(
      'Turn 1 & 2/3: Misconception diagnosis, suggestion chip progression, and 100% celebration',
      (tester) async {
        final fakeService = FakeTeachingApiService();

        // Build the InteractiveTeacherScreen inside a MaterialApp harness
        await tester.pumpWidget(
          MaterialApp(
            theme: ThemeData.dark(),
            home: InteractiveTeacherScreen(
              topic: 'Rational Agents',
              subject: 'Artificial Intelligence',
              apiService: fakeService,
            ),
          ),
        );

        // Wait for session initiation
        await tester.pumpAndSettle();

        // =====================================================================
        // SCENARIO 1: Turn 1 - Prior knowledge probe & Misconception Diagnosis
        // =====================================================================
        // 1. Confirm the prior-knowledge assessment prompt appears
        expect(
          find.textContaining('what do you already know about rational agents'),
          findsOneWidget,
        );

        // 2. Enter misconception: "A rational agent is just one that runs on a fast CPU"
        final answerField = find.byKey(const Key('teacher_answer_field'));
        expect(answerField, findsOneWidget);
        await tester.enterText(
          answerField,
          'A rational agent is just one that runs on a fast CPU',
        );
        await tester.pumpAndSettle();

        // 3. Tap Send button
        final sendButton = find.byKey(const Key('teacher_send_button'));
        expect(sendButton, findsOneWidget);
        await tester.tap(sendButton);
        await tester.pumpAndSettle(const Duration(seconds: 1));

        // 4. Assert misconception badge and analogy appear
        expect(find.byKey(const Key('misconception_badge')), findsOneWidget);
        expect(
          find.textContaining('Common Misconception Identified'),
          findsOneWidget,
        );
        expect(
          find.textContaining('fast race car heading in the wrong direction'),
          findsOneWidget,
        );

        // =====================================================================
        // SCENARIO 2: Turn 2 & 3 - Advance via Suggestion Chips to 100% Mastery
        // =====================================================================
        // 1. Turn 2: Tap first suggestion chip to answer the remediation probe
        final firstChip = find.byKey(const Key('suggestion_chip_0'));
        expect(firstChip, findsOneWidget);
        await tester.tap(firstChip);
        await tester.pumpAndSettle(const Duration(seconds: 1));

        // Assert Step 2 (PEAS Framework) appears
        expect(find.text('PEAS Framework'), findsOneWidget);
        expect(find.text('Mastery: 65%'), findsOneWidget);

        // 2. Turn 3: Tap suggestion chip "Performance Measure" to solve final check
        final peasChip = find.byKey(const Key('suggestion_chip_0'));
        expect(peasChip, findsOneWidget);
        await tester.tap(peasChip);
        await tester.pumpAndSettle(const Duration(seconds: 1));

        // 3. Assert celebration view appears and mastery reaches 100%
        expect(
          find.byKey(const Key('mastery_celebration_view')),
          findsOneWidget,
        );
        expect(find.text('Mastery: 100%'), findsOneWidget);
        expect(
          find.textContaining('100% Complete'),
          findsOneWidget,
        );

        // 4. Capture screenshot on celebration screen
        try {
          await binding.takeScreenshot('mastery_celebration_screen');
        } catch (_) {
          // Gracefully handles environments without external driver screenshot sinks
        }
      },
    );

    // =========================================================================
    // SCENARIO 3: Offline Draft Preservation
    // =========================================================================
    testWidgets(
      'Offline draft preservation: network failure retains typed text and shows Retry SnackBar',
      (tester) async {
        final fakeService = FakeTeachingApiService();
        fakeService.simulateFailure = true;

        await tester.pumpWidget(
          MaterialApp(
            theme: ThemeData.dark(),
            home: InteractiveTeacherScreen(
              topic: 'Search Algorithms',
              subject: 'Artificial Intelligence',
              apiService: fakeService,
            ),
          ),
        );
        await tester.pumpAndSettle();

        // 1. Confirm session starts with answer field ready
        final answerField = find.byKey(const Key('teacher_answer_field'));
        expect(answerField, findsOneWidget);

        // 2. Type draft student answer
        const draftText = 'A* algorithm uses admissible heuristic estimates';
        await tester.enterText(answerField, draftText);
        await tester.pumpAndSettle();

        // 3. Tap Send button while simulated failure is active
        final sendButton = find.byKey(const Key('teacher_send_button'));
        expect(sendButton, findsOneWidget);
        await tester.tap(sendButton);
        await tester.pumpAndSettle();

        // 4. Assert draft text is safely preserved in the input field
        expect(find.text(draftText), findsOneWidget);

        // 5. Assert SnackBar with Retry action appeared
        expect(find.text('Retry'), findsOneWidget);
      },
    );
  });
}
