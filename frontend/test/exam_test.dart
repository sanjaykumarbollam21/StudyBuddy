import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/exam/models/exam_model.dart';
import 'package:frontend/features/exam/services/exam_api_service.dart';
import 'package:frontend/features/exam/screens/mock_exam_screen.dart';
import 'package:frontend/features/exam/screens/exam_result_screen.dart';
import 'package:frontend/features/teaching/screens/interactive_teacher_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 7 Exam Readiness & Mock Test Models and Service Tests', () {
    test('Exam models serialize and parse correctly', () {
      final question = MockExamQuestionModel(
        id: 'q-test-1',
        topic: 'Deadlocks',
        questionType: 'mcq',
        prompt: 'Which condition is NOT required for deadlock?',
        options: ['Mutual Exclusion', 'Preemption Allowed', 'Hold and Wait', 'Circular Wait'],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 1,
        difficulty: 'intermediate',
        conceptTag: 'coffman_conditions',
      );

      expect(question.id, equals('q-test-1'));
      expect(question.topic, equals('Deadlocks'));
      expect(question.marks, equals(10.0));
      expect(question.negativeMarks, equals(2.5));
      expect(question.options.length, equals(4));

      final session = MockExamSessionModel(
        id: 'sess-101',
        title: 'Operating Systems Semester Exam — Mock Session',
        subject: 'Operating Systems',
        durationMinutes: 45,
        timeRemainingSeconds: 2700,
        totalQuestions: 6,
        totalMarks: 60.0,
        questions: [question],
      );

      expect(session.id, equals('sess-101'));
      expect(session.durationMinutes, equals(45));
      expect(session.totalQuestions, equals(6));
      expect(session.questions.first.prompt, contains('NOT required'));

      final result = ExamResultModel(
        id: 'res-101',
        title: 'Operating Systems Exam Results',
        status: 'submitted',
        scorePercentage: 74.0,
        marksObtained: 44.4,
        totalMarks: 60.0,
        negativeMarksDeducted: 2.5,
        correctCount: 4,
        incorrectCount: 1,
        unansweredCount: 1,
        topicAnalysis: [
          TopicPerformanceModel(
            topic: 'CPU Scheduling',
            scorePercentage: 89.0,
            tier: 'Strong',
            correctCount: 1,
            questionCount: 1,
            marksObtained: 10.0,
            totalMarks: 10.0,
          ),
          TopicPerformanceModel(
            topic: 'Deadlocks',
            scorePercentage: 31.0,
            tier: 'Critical',
            correctCount: 0,
            questionCount: 2,
            marksObtained: 3.1,
            totalMarks: 20.0,
          ),
        ],
        cognitiveDiagnosis: CognitiveDiagnosisModel(
          coreIssue: "Your biggest problem isn't memorization. Your answers show confusion between deadlock prevention and deadlock avoidance.",
          deepExplanation: "Deadlock Prevention statically eliminates Coffman conditions; Avoidance uses dynamic lookahead.",
          keyRemediationConcept: 'Deadlock Prevention vs Avoidance',
        ),
        remediationAction: RemediationActionModel(
          targetTopic: 'Deadlocks',
          ctaTitle: 'Reteach Deadlocks',
          prompt: 'Teach me the core difference between prevention and avoidance.',
          learningObjective: 'Master deadlock prevention versus avoidance.',
        ),
        readiness: ExamReadinessDetailModel(
          readinessPercentage: 68.0,
          readinessCategory: 'Moderate Exam Readiness',
          readinessMessage: "You're approximately 68% ready for this exam.",
          actionableProjection: "Spend your next 3 sessions on Synchronization and Deadlocks.",
          dimensionScores: {'knowledge_coverage': 85.0, 'concept_mastery': 62.0},
        ),
      );

      expect(result.scorePercentage, equals(74.0));
      expect(result.marksObtained, equals(44.4));
      expect(result.readiness.readinessPercentage, equals(68.0));
      expect(result.cognitiveDiagnosis.coreIssue, contains("confusion between deadlock prevention and deadlock avoidance"));
      expect(result.topicAnalysis.length, equals(2));
      expect(result.topicAnalysis[1].tier, equals('Critical'));
    });

    test('ExamApiService returns fallback mock session and readiness projections', () async {
      final api = ExamApiService();

      final session = await api.startMockExam(subject: 'Operating Systems', totalQuestions: 6);
      expect(session.questions.isNotEmpty, isTrue);
      expect(session.subject, equals('Operating Systems'));
      expect(session.durationMinutes, equals(45));

      final readiness = await api.getExamReadiness();
      expect(readiness.readinessPercentage, greaterThan(50.0));
      expect(readiness.readinessMessage, contains('ready for this exam'));
      expect(readiness.actionableProjection, contains('sessions'));
    });
  });

  group('Phase 7 MockExamScreen & ExamResultScreen Widget Tests', () {
    testWidgets('MockExamScreen renders timer, navigation palette, answers options and triggers submit dialog', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: MockExamScreen(
            subject: 'Operating Systems',
            totalQuestions: 6,
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Header & Timer
      expect(find.textContaining('Mock Session'), findsOneWidget);
      expect(find.byIcon(Icons.timer_outlined), findsOneWidget);

      // Verify Palette
      expect(find.textContaining('QUESTION PALETTE'), findsOneWidget);

      // Verify Options are visible
      expect(find.textContaining('Deadlock Prevention'), findsWidgets);

      // Select an option
      final firstOption = find.textContaining('statically').first;
      await tester.tap(firstOption);
      await tester.pumpAndSettle();

      // Flag for review
      final flagButton = find.text('Flag');
      expect(flagButton, findsOneWidget);
      await tester.tap(flagButton);
      await tester.pumpAndSettle();
      expect(find.widgetWithText(OutlinedButton, 'Flagged'), findsOneWidget);

      // Open Submit Confirmation Dialog
      final submitButton = find.text('Submit');
      expect(submitButton, findsOneWidget);
      await tester.tap(submitButton);
      await tester.pumpAndSettle();

      // Verify Confirmation Dialog contents
      expect(find.text('Submit Examination?'), findsOneWidget);
      expect(find.text('Answered'), findsNWidgets(2));
      expect(find.text('Marked for Review'), findsOneWidget);
      expect(find.text('Submit & View Results'), findsOneWidget);
    });

    testWidgets('ExamResultScreen renders overall score, readiness, cognitive diagnosis and launches Socratic Teacher CTA', (WidgetTester tester) async {
      final api = ExamApiService();
      final sampleResult = await api.submitMockExam('sample-sess-id');

      await tester.pumpWidget(
        MaterialApp(
          home: ExamResultScreen(result: sampleResult),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Overall Score & Readiness Hero
      expect(find.text('OVERALL SCORE'), findsOneWidget);
      expect(find.text('74%'), findsOneWidget);
      expect(find.text('ESTIMATED READINESS'), findsOneWidget);
      expect(find.text('68%'), findsOneWidget);

      // Verify Cognitive Diagnostic Card
      expect(find.text('COGNITIVE DIAGNOSIS'), findsOneWidget);
      expect(find.textContaining('deadlock prevention and deadlock avoidance'), findsOneWidget);

      // Verify Topic Breakdown
      expect(find.text('Topic Performance Breakdown'), findsOneWidget);
      expect(find.text('CPU Scheduling'), findsOneWidget);
      expect(find.text('Deadlocks'), findsWidgets);

      // Verify Closed-Loop Reteach CTA
      final reteachButton = find.text('Reteach Deadlocks');
      expect(reteachButton, findsOneWidget);

      // Scroll to CTA and tap
      await tester.ensureVisible(reteachButton);
      await tester.pumpAndSettle();
      await tester.tap(reteachButton);
      await tester.pumpAndSettle();

      // Verify Socratic Teacher Screen opened
      expect(find.byType(InteractiveTeacherScreen), findsOneWidget);
      expect(find.text('Deadlocks'), findsWidgets);
    });
  });
}
