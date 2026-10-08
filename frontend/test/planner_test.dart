import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/planner/models/planner_model.dart';
import 'package:frontend/features/planner/services/planner_api_service.dart';
import 'package:frontend/features/planner/screens/study_planner_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 9 Study Planner & Agent Models Tests', () {
    test('StudyPlanModel & StudyPlanItemModel serialization & deserialization', () {
      final item = StudyPlanItemModel(
        id: 'item-101',
        planId: 'plan-101',
        dayNumber: 1,
        sessionType: 'learn',
        topic: 'Deadlocks & Concurrency',
        allocatedMinutes: 60,
        priorityWeight: 0.95,
        status: 'pending',
        actionType: 'socratic_lesson',
        actionPayload: {'topic': 'Deadlocks', 'subject': 'Operating Systems'},
      );

      final jsonItem = item.toJson();
      expect(jsonItem['id'], equals('item-101'));
      expect(jsonItem['session_type'], equals('learn'));
      expect(jsonItem['priority_weight'], equals(0.95));

      final parsedItem = StudyPlanItemModel.fromJson(jsonItem);
      expect(parsedItem.topic, equals('Deadlocks & Concurrency'));
      expect(parsedItem.allocatedMinutes, equals(60));

      final plan = StudyPlanModel(
        id: 'plan-101',
        title: 'OS Final Prep Plan',
        subject: 'Operating Systems',
        dailyStudyMinutes: 120,
        totalDays: 12,
        totalAvailableHours: 24.0,
        currentDay: 1,
        status: 'active',
        strategySummary: {'rationale': '4-phase mastery trajectory'},
        items: [parsedItem],
        todayItems: [parsedItem],
        progressPercentage: 20.0,
      );

      final jsonPlan = plan.toJson();
      expect(jsonPlan['total_available_hours'], equals(24.0));
      expect(jsonPlan['items'].length, equals(1));

      final parsedPlan = StudyPlanModel.fromJson(jsonPlan);
      expect(parsedPlan.id, equals('plan-101'));
      expect(parsedPlan.totalDays, equals(12));
      expect(parsedPlan.todayItems.first.topic, contains('Deadlocks'));
    });

    test('AgentChatResponseModel and MicroSessionModel serialization', () {
      final agentRes = AgentChatResponseModel(
        message: '30-minute practice session configured.',
        intent: 'micro_session',
        reasoning: 'Targeted drill on lowest-mastery topic.',
        suggestedAction: AgentActionPayloadModel(
          actionType: 'practice_quiz',
          topic: 'Deadlocks',
          subject: 'Operating Systems',
          durationMinutes: 30,
        ),
      );

      final json = agentRes.toJson();
      expect(json['intent'], equals('micro_session'));
      expect(json['suggested_action']['topic'], equals('Deadlocks'));

      final parsed = AgentChatResponseModel.fromJson(json);
      expect(parsed.suggestedAction?.durationMinutes, equals(30));

      final micro = MicroSessionModel(
        allocatedMinutes: 20,
        recommendedTopic: 'Coffman Conditions',
        sessionType: 'revision',
        actionType: 'active_recall',
        pedagogicalReasoning: 'Rapid-fire active recall queue.',
      );

      expect(micro.allocatedMinutes, equals(20));
      expect(micro.actionType, equals('active_recall'));
    });
  });

  group('Phase 9 PlannerApiService Offline-First Fallbacks Tests', () {
    final apiService = PlannerApiService();

    test('getActivePlan returns multi-phase 12-day plan with scheduled items', () async {
      final plan = await apiService.getActivePlan(subject: 'Operating Systems');

      expect(plan.subject, equals('Operating Systems'));
      expect(plan.totalDays, equals(12));
      expect(plan.totalAvailableHours, equals(24.0));
      expect(plan.items.isNotEmpty, isTrue);
      expect(plan.todayItems.isNotEmpty, isTrue);
      expect(plan.todayItems.first.topic, contains('Deadlocks'));
    });

    test('getMicroSession optimizes mode based on duration', () async {
      // 15 mins -> active recall
      final micro15 = await apiService.getMicroSession(15);
      expect(micro15.sessionType, equals('revision'));
      expect(micro15.actionType, equals('active_recall'));

      // 30 mins -> practice drill
      final micro30 = await apiService.getMicroSession(30);
      expect(micro30.sessionType, equals('practice'));
      expect(micro30.actionType, equals('practice_quiz'));

      // 60 mins -> socratic lesson
      final micro60 = await apiService.getMicroSession(60);
      expect(micro60.sessionType, equals('learn'));
      expect(micro60.actionType, equals('socratic_lesson'));
    });

    test('replan gracefully absorbs missed days without failing student', () async {
      final replanned = await apiService.replan(missedDays: 2);

      expect(replanned.currentDay, equals(3));
      expect(replanned.totalDays, equals(10));
      expect(replanned.strategySummary['replan_reason'], contains('Absorbed 2 missed day'));
      expect(replanned.strategySummary['rationale'], contains('gracefully'));
    });

    test('sendAgentMessage interprets natural language conversational prompts', () async {
      final res1 = await apiService.sendAgentMessage('I have 30 minutes');
      expect(res1.intent, equals('micro_session'));
      expect(res1.suggestedAction?.durationMinutes, equals(30));

      final res2 = await apiService.sendAgentMessage('I missed yesterday');
      expect(res2.intent, equals('handle_missed_day'));
      expect(res2.message, contains('Schedule Re-calculated'));

      final res3 = await apiService.sendAgentMessage('Focus on weak areas');
      expect(res3.intent, equals('focus_weak_areas'));
      expect(res3.message, contains('Weak-Area Prioritization'));
    });
  });

  group('Phase 9 StudyPlannerScreen Widget Tests', () {
    testWidgets('renders planner status hub, agent companion card, and today plan', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: StudyPlannerScreen(subject: 'Operating Systems'),
        ),
      );

      // Pump to resolve future
      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump(const Duration(milliseconds: 300));

      // 1. Verify AppBar and Title
      expect(find.text('Intelligent Study Planner & AI Agent'), findsOneWidget);
      expect(find.textContaining('Proactive Autonomous Learning Coordinator'), findsOneWidget);

      // 2. Verify Status Hub & Pacing
      expect(find.textContaining('AI STUDY PLANNER AGENT'), findsOneWidget);
      expect(find.textContaining('DAY 1 OF 12'), findsOneWidget);
      expect(find.textContaining('24.0h AVAILABLE'), findsOneWidget);

      // 3. Verify Agent Card and Prompts
      expect(find.text('Study Buddy Autonomous Agent'), findsOneWidget);
      expect(find.text('What should I study now?'), findsOneWidget);
      expect(find.text('I have 30 minutes'), findsOneWidget);
      expect(find.text('I missed yesterday'), findsOneWidget);

      // 4. Verify Today\'s Priority Action Plan
      expect(find.textContaining('Today\'s Priority Action Plan'), findsOneWidget);
      expect(find.text('Deadlocks & Concurrency'), findsWidgets);
      expect(find.text('Launch LEARN'), findsOneWidget);

      // 5. Verify Long-Term Trajectory Roadmap
      expect(find.text('Dynamic Long-Term Trajectory'), findsOneWidget);
    });

    testWidgets('tapping quick prompt chip triggers agent response and action button', (WidgetTester tester) async {
      tester.view.physicalSize = const Size(1000, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      await tester.pumpWidget(
        const MaterialApp(
          home: StudyPlannerScreen(subject: 'Operating Systems'),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump(const Duration(milliseconds: 300));

      // Tap "I have 30 minutes" prompt chip
      final chip30 = find.text('I have 30 minutes');
      expect(chip30, findsOneWidget);
      await tester.tap(chip30);
      await tester.pump(const Duration(milliseconds: 300));

      // Verify agent message updated with 30-minute micro session
      expect(find.textContaining('30-Minute Micro-Session Configured'), findsOneWidget);

      // Verify immediate action execution button appeared
      expect(find.textContaining('Execute Action: PRACTICE QUIZ (Deadlocks)'), findsOneWidget);
    });

    testWidgets('replan modal opens and recalculates timeline', (WidgetTester tester) async {
      tester.view.physicalSize = const Size(1000, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      await tester.pumpWidget(
        const MaterialApp(
          home: StudyPlannerScreen(subject: 'Operating Systems'),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));
      await tester.pump(const Duration(milliseconds: 300));

      // Tap "Replan Schedule" button
      final replanBtn = find.text('Replan Schedule');
      expect(replanBtn, findsOneWidget);
      await tester.tap(replanBtn);
      await tester.pumpAndSettle();

      // Verify modal opened
      expect(find.text('🔄 Dynamic Re-Plan Agent'), findsOneWidget);
      expect(find.text('Did you miss any study days?'), findsOneWidget);
      expect(find.text('2 days missed'), findsOneWidget);

      // Select 2 days missed and submit
      final twoDaysChip = find.text('2 days missed');
      await tester.tap(twoDaysChip);
      await tester.pump(const Duration(milliseconds: 100));

      final calcBtn = find.text('Recalculate & Optimize Timetable');
      await tester.tap(calcBtn);
      await tester.pumpAndSettle();

      // Verify modal dismissed and day counter updated to Day 3
      expect(find.text('🔄 Dynamic Re-Plan Agent'), findsNothing);
      expect(find.textContaining('DAY 3 OF 10'), findsOneWidget);
    });
  });
}
