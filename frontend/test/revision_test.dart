import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/revision/models/revision_model.dart';
import 'package:frontend/features/revision/services/revision_api_service.dart';
import 'package:frontend/features/revision/screens/active_recall_screen.dart';
import 'package:frontend/features/dashboard/screens/home_tab.dart';
import 'package:frontend/features/auth/controllers/auth_controller.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 6 Spaced Repetition Models and Service Tests', () {
    test('RevisionItemModel and DailyAgendaModel serialize correctly', () {
      final item = RevisionItemModel(
        id: 'rev-test-1',
        topicTitle: 'Deadlocks',
        conceptSummary: 'Mutual blocking',
        retrievalPrompt: 'Name all 4 Coffman conditions from memory',
        retrievalAnswer: 'Mutual exclusion, hold and wait, no preemption, circular wait',
        intervalDays: 6,
        repetitionCount: 2,
        easeFactor: 2.6,
        masteryScore: 78.0,
        daysOverdue: 1.5,
        qualityHistory: [4, 4],
      );

      expect(item.id, equals('rev-test-1'));
      expect(item.topicTitle, equals('Deadlocks'));
      expect(item.retrievalPrompt, contains('Coffman conditions'));
      expect(item.intervalDays, equals(6));

      final agenda = DailyAgendaModel(
        continueLearning: ContinueLearningInfoModel(
          topic: 'Deadlocks',
          progressText: 'Step 3 of 5',
          subject: 'Operating Systems',
        ),
        dueForReviewCount: 4,
        topWeakArea: WeakAreaInfoModel(
          concept: 'Circular Wait',
          masteryPercentage: 42.0,
          topic: 'Deadlocks',
        ),
        recommendedAction: '5-minute active retrieval',
        examPriority: 'CPU Scheduling',
        reviewStreakDays: 5,
        retentionRatePercentage: 88.0,
      );

      expect(agenda.dueForReviewCount, equals(4));
      expect(agenda.topWeakArea.concept, equals('Circular Wait'));
      expect(agenda.continueLearning.topic, equals('Deadlocks'));
    });

    test('RevisionApiService retrieves fallback due items and agenda', () async {
      final api = RevisionApiService();

      final dueItems = await api.getDueReviews(limit: 5);
      expect(dueItems.isNotEmpty, isTrue);
      expect(dueItems[0].retrievalPrompt, isNotEmpty);

      final agenda = await api.getDailyAgenda();
      expect(agenda.dueForReviewCount, greaterThan(0));
      expect(agenda.topWeakArea.concept, isNotEmpty);

      final reviewRes = await api.submitReview(
        itemId: dueItems[0].id,
        qualityRating: 4,
      );
      expect(reviewRes.isPassed, isTrue);
      expect(reviewRes.newIntervalDays, greaterThanOrEqualTo(1));
    });
  });

  group('Phase 6 ActiveRecallScreen Widget Tests', () {
    testWidgets('ActiveRecallScreen displays retrieval probe, reveals answer, and accepts rating', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: ActiveRecallScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Header and Active Challenge
      expect(find.text('Active Recall & Retrieval'), findsOneWidget);
      expect(find.text('ACTIVE RETRIEVAL PROBE'), findsOneWidget);
      expect(find.textContaining('Coffman deadlock conditions'), findsOneWidget);

      // Verify Reveal Button
      final revealButton = find.text('Reveal Key Concepts & Verify Recall');
      expect(revealButton, findsOneWidget);

      // Tap Reveal Button
      await tester.tap(revealButton);
      await tester.pumpAndSettle();

      // Verify Canonical Answer is revealed
      expect(find.text('Key Canonical Concepts'), findsOneWidget);
      expect(find.textContaining('Mutual Exclusion'), findsOneWidget);

      // Verify Rating Buttons are visible
      final perfectButton = find.text('Perfect Recall (5)');
      expect(perfectButton, findsOneWidget);
      expect(find.text('Failed Recall (2)'), findsOneWidget);

      // Scroll to Perfect Recall and tap
      await tester.ensureVisible(perfectButton);
      await tester.pumpAndSettle();
      await tester.tap(perfectButton);
      await tester.pumpAndSettle();

      // Verify Next Review interval scheduled
      expect(find.textContaining('Next review scheduled in'), findsOneWidget);
    });
  });

  group('Phase 6 HomeTab Today\'s Learning Hub Widget Tests', () {
    testWidgets('HomeTab renders Today\'s Learning Plan with Due count and Weak area', (WidgetTester tester) async {
      SharedPreferences.setMockInitialValues({});
      final authController = AuthController();
      await authController.initialize();
      await authController.loginWithDemoAccount();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HomeTab(
              authController: authController,
              onTabNavigate: (_) {},
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Greeting
      expect(find.textContaining('Sanjay'), findsWidgets);

      // Verify "Today's Learning Plan" Hub
      expect(find.text("Today's Learning Plan"), findsOneWidget);
      expect(find.text('Due for Review'), findsOneWidget);
      expect(find.text('Start Active Recall'), findsOneWidget);
      expect(find.text('Weak Area Alert'), findsOneWidget);
      expect(find.textContaining('Circular Wait'), findsOneWidget);
      expect(find.text('Fix Weak Concept'), findsOneWidget);

      // Verify Continue Learning Roadmap Hero
      expect(find.text('CONTINUE LEARNING'), findsOneWidget);
      expect(find.text('Resume With AI Teacher'), findsOneWidget);
    });
  });
}
