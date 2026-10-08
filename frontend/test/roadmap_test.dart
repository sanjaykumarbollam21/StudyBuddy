import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/roadmap/models/roadmap_model.dart';
import 'package:frontend/features/roadmap/services/roadmap_api_service.dart';
import 'package:frontend/features/dashboard/screens/learn_tab.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Phase 4B Roadmap Models & Service Tests', () {
    test('RoadmapTopicModel and RoadmapModel parse and serialize correctly', () {
      final topic = RoadmapTopicModel(
        orderIndex: 1,
        customTitle: 'Processes & Lifecycle',
        description: 'Process states, PCB, context switching',
        difficulty: 'beginner',
        estimatedMinutes: 45,
        status: 'in_progress',
        masteryScore: 40.0,
        prerequisites: ['OS Fundamentals & Architecture'],
        learningObjectives: ['Diagram 5 states', 'Explain PCB'],
      );

      expect(topic.isInProgress, isTrue);
      expect(topic.isLocked, isFalse);
      expect(topic.isMastered, isFalse);
      expect(topic.isUnlocked, isTrue);
      expect(topic.prerequisites, contains('OS Fundamentals & Architecture'));

      final roadmap = RoadmapModel(
        id: 'lp-test-1',
        title: 'Operating Systems Mastery Track',
        subject: 'Operating Systems',
        goal: 'Ace Systems Interview',
        totalSteps: 5,
        completedSteps: 2,
        progressPercentage: 40.0,
        status: 'in_progress',
        topics: [topic],
      );

      expect(roadmap.totalSteps, equals(5));
      expect(roadmap.completedSteps, equals(2));
      expect(roadmap.topics.length, equals(1));
      expect(roadmap.topics.first.customTitle, equals('Processes & Lifecycle'));
    });

    test('RoadmapApiService retrieves fallback curriculum, recommendations, and why rationales', () async {
      final api = RoadmapApiService();

      // 1. Generate fallback roadmap
      final roadmap = await api.generateRoadmap(subject: 'Operating Systems');
      expect(roadmap.topics.isNotEmpty, isTrue);
      expect(roadmap.topics[0].customTitle, contains('OS Fundamentals'));

      // 2. Next Recommendation
      final nextRec = await api.getNextRecommendation();
      expect(nextRec.topicTitle, isNotEmpty);
      expect(nextRec.whyRecommended, isNotEmpty);

      // 3. Why Learning rationale
      final why = await api.getWhyLearning(topic: 'Deadlocks & Banker\'s Algorithm');
      expect(why.topicTitle, equals('Deadlocks & Banker\'s Algorithm'));
      expect(why.fullExplanation, isNotEmpty);
      expect(why.coreValue, isNotEmpty);
    });
  });

  group('Phase 4B LearnTab Knowledge Graph Roadmap Widget Tests', () {
    testWidgets('LearnTab renders tracks, next recommendation card, and roadmap milestones', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LearnTab(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // 1. Verify title and description
      expect(find.text('Intelligent Curriculum & Roadmaps'), findsOneWidget);
      expect(find.textContaining('Knowledge-graph powered learning paths'), findsOneWidget);

      // 2. Verify track selection chips
      expect(find.text('Operating Systems'), findsWidgets);
      expect(find.text('Database Management Systems'), findsOneWidget);
      expect(find.text('Machine Learning'), findsOneWidget);
      expect(find.text('Python & Data Structures'), findsOneWidget);

      // 3. Verify Hero "RECOMMENDED NEXT STEP" Card
      expect(find.text('RECOMMENDED NEXT STEP'), findsOneWidget);
      expect(find.text('Start Socratic Lesson'), findsOneWidget);
      expect(find.text('Why learn this?'), findsWidgets);

      // 4. Verify Roadmap milestones list
      expect(find.textContaining('OS Fundamentals & Architecture'), findsWidgets);
      expect(find.textContaining('Processes & Lifecycle'), findsWidgets);
      expect(find.textContaining('Deadlocks & Banker\'s Algorithm'), findsWidgets);

      // 5. Scroll and tap locked button to verify Prerequisite Dialog
      final lockedButton = find.widgetWithText(OutlinedButton, 'Locked').first;
      await tester.ensureVisible(lockedButton);
      await tester.pumpAndSettle();

      await tester.tap(lockedButton);
      await tester.pumpAndSettle();

      expect(find.text('Prerequisites Required'), findsOneWidget);
      expect(find.textContaining('Before starting'), findsOneWidget);
      expect(find.text('Understood'), findsOneWidget);

      // Dismiss dialog
      await tester.tap(find.text('Understood'));
      await tester.pumpAndSettle();
      expect(find.text('Prerequisites Required'), findsNothing);
    });
  });
}

