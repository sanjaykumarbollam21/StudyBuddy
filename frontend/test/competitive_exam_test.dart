import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/competitive_exam/models/competitive_exam_models.dart';
import 'package:frontend/features/competitive_exam/services/competitive_exam_service.dart';
import 'package:frontend/features/competitive_exam/screens/competitive_exam_dashboard_screen.dart';
import 'package:frontend/features/competitive_exam/screens/pyq_practice_screen.dart';
import 'package:frontend/features/competitive_exam/screens/current_affairs_screen.dart';
import 'package:frontend/features/competitive_exam/screens/mains_answer_writing_screen.dart';

void main() {
  group('Competitive Exam Models & Service Unit Tests', () {
    test('CompetitiveExamProfileModel json parsing', () {
      final json = {
        'id': 'profile-1',
        'exam_id': 'upsc_cse',
        'exam_name': 'UPSC CSE',
        'target_year': 2027,
        'current_stage': 'prelims',
        'daily_target_hours': 6.5,
        'language': 'English',
        'daf_details': {'graduation_major': 'Computer Science'},
      };

      final model = CompetitiveExamProfileModel.fromJson(json);
      expect(model.id, 'profile-1');
      expect(model.examId, 'upsc_cse');
      expect(model.targetYear, 2027);
      expect(model.dailyTargetHours, 6.5);
      expect(model.dafDetails['graduation_major'], 'Computer Science');
    });

    test('PYQModel and PYQOptionModel json parsing', () {
      final json = {
        'id': 'pyq-1',
        'exam_id': 'upsc_cse',
        'year': 2023,
        'stage': 'prelims',
        'paper_name': 'GS 1',
        'topic_title': 'Fundamental Rights',
        'question_text': 'What is Article 21?',
        'question_type': 'single_correct',
        'options': [
          {'label': 'A', 'text': 'Right to Life and Personal Liberty'},
          {'label': 'B', 'text': 'Right to Equality'},
        ],
        'correct_answer': 'A',
        'explanation': 'Article 21 guarantees right to life.',
        'marks': 2.0,
        'negative_marks': 0.66,
        'difficulty': 'medium',
      };

      final pyq = PYQModel.fromJson(json);
      expect(pyq.id, 'pyq-1');
      expect(pyq.options.length, 2);
      expect(pyq.options[0].label, 'A');
      expect(pyq.correctAnswer, 'A');
      expect(pyq.negativeMarks, 0.66);
    });

    test('CurrentAffairModel json parsing', () {
      final json = {
        'id': 'ca-1',
        'date': '2026-10-05',
        'title': 'Supreme Court Judgment',
        'category': 'Polity',
        'summary': 'Summary text',
        'background': 'Background text',
        'static_concepts': [
          {'concept': 'Article 20(3)', 'description': 'Self incrimination'},
        ],
        'prelims_pointers': ['Pointer 1'],
        'mains_pointers': ['Pointer 2'],
        'source': 'The Hindu',
      };

      final ca = CurrentAffairModel.fromJson(json);
      expect(ca.id, 'ca-1');
      expect(ca.staticConcepts.length, 1);
      expect(ca.staticConcepts[0].concept, 'Article 20(3)');
      expect(ca.prelimsPointers.length, 1);
    });

    test('MainsAnswerEvaluationModel json parsing', () {
      final json = {
        'word_count': 140,
        'word_limit': 150,
        'total_marks': 10.0,
        'marks_obtained': 6.5,
        'score_percentage': 65.0,
        'rubric_breakdown': {
          'content_accuracy': 70.0,
          'structural_flow': 75.0,
        },
        'strengths': ['Clear structure'],
        'missing_dimensions': ['Add case law'],
        'improvement_guidelines': 'Integrate examples',
        'model_outline': 'Intro - Body - Conclusion',
        'paper_name': 'GS 2',
      };

      final eval = MainsAnswerEvaluationModel.fromJson(json);
      expect(eval.wordCount, 140);
      expect(eval.marksObtained, 6.5);
      expect(eval.rubricBreakdown['content_accuracy'], 70.0);
      expect(eval.strengths.first, 'Clear structure');
    });

    test('ReadinessReportModel json parsing', () {
      final json = {
        'exam_id': 'upsc_cse',
        'exam_name': 'UPSC CSE',
        'target_year': 2027,
        'days_remaining': 100,
        'overall_preparation_percentage': 60.0,
        'readiness_radar': {
          'overall_readiness': 60.0,
          'concept_readiness': 65.0,
        },
        'today_priority': {'topic': 'Polity'},
        'topic_heatmap': {'coverage_percentage': 55.0},
      };

      final rep = ReadinessReportModel.fromJson(json);
      expect(rep.examId, 'upsc_cse');
      expect(rep.daysRemaining, 100);
      expect(rep.readinessRadar['concept_readiness'], 65.0);
    });

    test('CompetitiveExamService fallback getters return non-empty lists', () async {
      final service = CompetitiveExamService();
      final profiles = await service.getSupportedProfiles();
      expect(profiles.isNotEmpty, isTrue);

      final current = await service.getCurrentProfile();
      expect(current.examId, 'upsc_cse');

      final pyqs = await service.getPYQs();
      expect(pyqs.isNotEmpty, isTrue);

      final ca = await service.getCurrentAffairs();
      expect(ca.isNotEmpty, isTrue);

      final report = await service.getReadinessReport();
      expect(report.readinessRadar.isNotEmpty, isTrue);
    });
  });

  group('Competitive Exam Widget Tests', () {
    testWidgets('CompetitiveExamDashboardScreen renders correctly', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        const MaterialApp(
          home: CompetitiveExamDashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Competitive Exam Intelligence'), findsOneWidget);
      expect(find.text('Practice & Intelligence Hubs'), findsOneWidget);
      expect(find.text('PYQ Practice'), findsOneWidget);
      expect(find.text('Current Affairs'), findsOneWidget);
      expect(find.text('Mains Writing'), findsOneWidget);
      expect(find.text('CSAT Aptitude'), findsOneWidget);
    });

    testWidgets('PYQPracticeScreen renders questions and options', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: PYQPracticeScreen(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Previous Year Questions'), findsOneWidget);
      expect(find.textContaining('Q 1 of'), findsOneWidget);
      expect(find.text('Submit Answer'), findsOneWidget);
    });

    testWidgets('CurrentAffairsScreen renders feed and category filters', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: CurrentAffairsScreen(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Current Affairs & Static Linking'), findsOneWidget);
      expect(find.text('All'), findsOneWidget);
      expect(find.text('Polity'), findsOneWidget);
    });

    testWidgets('MainsAnswerWritingScreen renders editor and word counter', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: MainsAnswerWritingScreen(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Mains Answer Writing Evaluator'), findsOneWidget);
      expect(find.text('Mains Question Prompt'), findsOneWidget);
      expect(find.text('Your Answer Draft'), findsOneWidget);
      expect(find.text('Evaluate Answer across 8 Rubrics'), findsOneWidget);
    });
  });
}
