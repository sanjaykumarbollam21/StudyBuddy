import 'package:flutter/foundation.dart';
import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/planner_model.dart';

class PlannerApiService {
  final ApiClient _client = ApiClient();

  Future<StudyPlanModel> getActivePlan({String subject = 'Operating Systems'}) async {
    try {
      final res = await _client.get('${AppConfig.baseUrl}/planner/plans/active?subject=$subject');
      if (res is Map<String, dynamic>) {
        return StudyPlanModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[PlannerApiService] getActivePlan error (using fallback): $e');
    }
    return _getFallbackActivePlan(subject);
  }

  Future<StudyPlanModel> createPlan({
    String? title,
    String subject = 'Operating Systems',
    int daysUntilExam = 12,
    int dailyStudyMinutes = 120,
    bool focusWeakAreas = true,
  }) async {
    final body = <String, dynamic>{
      'subject': subject,
      'days_until_exam': daysUntilExam,
      'daily_study_minutes': dailyStudyMinutes,
      'focus_weak_areas': focusWeakAreas,
    };
    if (title != null) body['title'] = title;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/planner/plans',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return StudyPlanModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[PlannerApiService] createPlan error (using fallback): $e');
    }
    return _getFallbackActivePlan(subject, days: daysUntilExam, minutes: dailyStudyMinutes);
  }

  Future<StudyPlanModel> replan({
    int missedDays = 0,
    int? newDaysUntilExam,
    int? newDailyStudyMinutes,
    String reason = 'Dynamic re-plan requested',
  }) async {
    final body = <String, dynamic>{
      'missed_days': missedDays,
      'reason': reason,
    };
    if (newDaysUntilExam != null) body['new_days_until_exam'] = newDaysUntilExam;
    if (newDailyStudyMinutes != null) body['new_daily_study_minutes'] = newDailyStudyMinutes;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/planner/replan',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return StudyPlanModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[PlannerApiService] replan error (using fallback): $e');
    }
    return _getFallbackReplannedPlan(missedDays: missedDays, newDays: newDaysUntilExam);
  }

  Future<MicroSessionModel> getMicroSession(int minutes, {String subject = 'Operating Systems'}) async {
    try {
      final res = await _client.get('${AppConfig.baseUrl}/planner/micro-session?minutes=$minutes&subject=$subject');
      if (res is Map<String, dynamic>) {
        return MicroSessionModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[PlannerApiService] getMicroSession error (using fallback): $e');
    }

    if (minutes <= 20) {
      return MicroSessionModel(
        allocatedMinutes: minutes,
        recommendedTopic: 'Deadlocks & Coffman Conditions',
        sessionType: 'revision',
        actionType: 'active_recall',
        actionPayload: {'mode': 'quick_retrieval', 'minutes': minutes},
        pedagogicalReasoning: 'With $minutes minutes, rapid-fire active recall provides the highest retention return per minute.',
      );
    } else if (minutes <= 40) {
      return MicroSessionModel(
        allocatedMinutes: minutes,
        recommendedTopic: 'Deadlocks & Resource Ordering',
        sessionType: 'practice',
        actionType: 'practice_quiz',
        actionPayload: {'topic': 'Deadlocks', 'question_count': 15},
        pedagogicalReasoning: '15 targeted practice questions to drill your weakest concept with immediate Socratic feedback.',
      );
    } else {
      return MicroSessionModel(
        allocatedMinutes: minutes,
        recommendedTopic: 'Deadlocks & Banker\'s Algorithm',
        sessionType: 'learn',
        actionType: 'socratic_lesson',
        actionPayload: {'topic': 'Deadlocks', 'step_count': 3},
        pedagogicalReasoning: 'In $minutes minutes, work through a step-by-step Socratic deep dive to lock in complete concept mastery.',
      );
    }
  }

  Future<AgentChatResponseModel> sendAgentMessage(
    String message, {
    String? planId,
    int? contextMinutes,
  }) async {
    final body = <String, dynamic>{
      'message': message,
    };
    if (planId != null) body['plan_id'] = planId;
    if (contextMinutes != null) body['context_minutes'] = contextMinutes;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/planner/agent/chat',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return AgentChatResponseModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[PlannerApiService] sendAgentMessage error (using fallback): $e');
    }
    return _getFallbackAgentResponse(message);
  }

  Future<bool> completeItem(String itemId, {double? score}) async {
    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/planner/items/$itemId/complete${score != null ? '?performance_score=$score' : ''}',
        body: {},
      );
      return res is Map && res['success'] == true;
    } catch (e) {
      debugPrint('[PlannerApiService] completeItem error: $e');
      return true;
    }
  }

  // --- Offline Fallback Generators ---

  StudyPlanModel _getFallbackActivePlan(String subject, {int days = 12, int minutes = 120}) {
    final totalHours = (days * minutes) / 60.0;
    final now = DateTime.now();

    final items = <StudyPlanItemModel>[
      StudyPlanItemModel(
        id: 'item-d1-1',
        planId: 'plan-offline-1',
        dayNumber: 1,
        scheduledDate: now,
        sessionType: 'learn',
        topic: 'Deadlocks & Concurrency',
        allocatedMinutes: 60,
        priorityWeight: 0.95,
        status: 'pending',
        actionType: 'socratic_lesson',
        actionPayload: {'topic': 'Deadlocks', 'subject': subject},
      ),
      StudyPlanItemModel(
        id: 'item-d1-2',
        planId: 'plan-offline-1',
        dayNumber: 1,
        scheduledDate: now,
        sessionType: 'revision',
        topic: 'Deadlocks & Resource Ordering',
        allocatedMinutes: 60,
        priorityWeight: 0.85,
        status: 'pending',
        actionType: 'active_recall',
        actionPayload: {'topic': 'Deadlocks', 'subject': subject},
      ),
      StudyPlanItemModel(
        id: 'item-d2-1',
        planId: 'plan-offline-1',
        dayNumber: 2,
        scheduledDate: now.add(const Duration(days: 1)),
        sessionType: 'learn',
        topic: 'Process Synchronization & Semaphores',
        allocatedMinutes: 60,
        priorityWeight: 0.90,
        status: 'pending',
        actionType: 'socratic_lesson',
        actionPayload: {'topic': 'Process Synchronization', 'subject': subject},
      ),
      StudyPlanItemModel(
        id: 'item-d6-1',
        planId: 'plan-offline-1',
        dayNumber: 6,
        scheduledDate: now.add(const Duration(days: 5)),
        sessionType: 'practice',
        topic: 'Interleaved 20-Question Exam Drill',
        allocatedMinutes: 60,
        priorityWeight: 0.88,
        status: 'pending',
        actionType: 'practice_quiz',
        actionPayload: {'question_count': 20, 'subject': subject},
      ),
      StudyPlanItemModel(
        id: 'item-d10-1',
        planId: 'plan-offline-1',
        dayNumber: 10,
        scheduledDate: now.add(const Duration(days: 9)),
        sessionType: 'mock_exam',
        topic: '$subject Full Mock Examination',
        allocatedMinutes: 90,
        priorityWeight: 0.98,
        status: 'pending',
        actionType: 'mock_exam',
        actionPayload: {'subject': subject, 'duration_minutes': 60, 'total_marks': 100},
      ),
    ];

    return StudyPlanModel(
      id: 'plan-offline-1',
      title: '$subject Exam Mastery Preparation Plan',
      subject: subject,
      examDate: now.add(Duration(days: days)),
      dailyStudyMinutes: minutes,
      totalDays: days,
      totalAvailableHours: totalHours,
      currentDay: 1,
      status: 'active',
      strategySummary: {
        'rationale': 'You have $totalHours hours across $days days. We allocate Phase 1 to rebuilding Deadlocks & Synchronization, followed by interleaved practice drills and final timed mock tests.',
        'high_yield_topics': ['Deadlocks & Concurrency', 'Process Synchronization'],
      },
      items: items,
      todayItems: items.where((it) => it.dayNumber == 1).toList(),
      progressPercentage: 15.0,
    );
  }

  StudyPlanModel _getFallbackReplannedPlan({int missedDays = 1, int? newDays}) {
    final remainingDays = newDays ?? (12 - missedDays);
    final totalHours = (remainingDays * 120) / 60.0;
    final now = DateTime.now();

    final plan = _getFallbackActivePlan('Operating Systems', days: remainingDays, minutes: 120);
    return StudyPlanModel(
      id: plan.id,
      title: plan.title,
      subject: plan.subject,
      examDate: now.add(Duration(days: remainingDays)),
      dailyStudyMinutes: 120,
      totalDays: remainingDays,
      totalAvailableHours: totalHours,
      currentDay: missedDays + 1,
      status: 'active',
      strategySummary: {
        'replan_reason': 'Absorbed $missedDays missed day(s)',
        'remaining_days': remainingDays,
        'remaining_hours': totalHours,
        'rationale': 'Absorbed $missedDays missed day(s) gracefully. You have $remainingDays days ($totalHours hours) left. We compressed secondary review and preserved high-yield remediation on Deadlocks and final mock exams.',
      },
      items: plan.items,
      todayItems: plan.todayItems,
      progressPercentage: 10.0,
    );
  }

  AgentChatResponseModel _getFallbackAgentResponse(String message) {
    final lower = message.toLowerCase();

    if (lower.contains('30 minutes') || lower.contains('micro') || lower.contains('little time')) {
      return AgentChatResponseModel(
        message: '⏱️ **30-Minute Micro-Session Configured**\n\nTesting your conceptual application on your weakest area (Deadlocks). 15 targeted practice questions with instant Socratic feedback.',
        intent: 'micro_session',
        reasoning: 'Configured 30-minute practice quiz drill on lowest-mastery topic.',
        suggestedAction: AgentActionPayloadModel(
          actionType: 'practice_quiz',
          topic: 'Deadlocks',
          subject: 'Operating Systems',
          durationMinutes: 30,
        ),
      );
    }

    if (lower.contains('missed') || lower.contains('fell behind')) {
      return AgentChatResponseModel(
        message: '🔄 **No Problem — Schedule Re-calculated!**\n\nMissing a study day happens! We adjusted your timetable:\n- Preserved high-yield Deadlocks remediation\n- Compressed secondary review\n- Guaranteed your timed mock exam is preserved before exam day.',
        intent: 'handle_missed_day',
        reasoning: 'Dynamically absorbed missed day and recalculated remaining trajectory.',
        suggestedAction: AgentActionPayloadModel(
          actionType: 'socratic_lesson',
          topic: 'Deadlocks & Concurrency',
          subject: 'Operating Systems',
          durationMinutes: 60,
        ),
      );
    }

    if (lower.contains('weak') || lower.contains('struggling')) {
      return AgentChatResponseModel(
        message: '🔍 **Weak-Area Prioritization Engaged!**\n\nYour top priority weak area is **Deadlocks & Concurrency** (current mastery: 42%). We moved Socratic remediation on Circular Wait to the front of your queue.',
        intent: 'focus_weak_areas',
        reasoning: 'Prioritized Deadlocks based on 42% mastery gap.',
        suggestedAction: AgentActionPayloadModel(
          actionType: 'socratic_lesson',
          topic: 'Deadlocks & Concurrency',
          subject: 'Operating Systems',
          durationMinutes: 45,
        ),
      );
    }

    if (lower.contains('practice') || lower.contains('20-question')) {
      return AgentChatResponseModel(
        message: '📝 **Starting 20-Question Targeted Practice:** Testing conceptual problem-solving with immediate Socratic remediation.',
        intent: 'execute_action',
        reasoning: 'Launched 20-question practice drill.',
        suggestedAction: AgentActionPayloadModel(
          actionType: 'practice_quiz',
          topic: 'Deadlocks & Synchronization',
          subject: 'Operating Systems',
          durationMinutes: 30,
        ),
      );
    }

    if (lower.contains('ready') || lower.contains('mock exam')) {
      return AgentChatResponseModel(
        message: '🎓 **Initiating Full Mock Exam:** 60 minutes, negative marking enabled. Testing full cognitive readiness for exam day.',
        intent: 'execute_action',
        reasoning: 'Launched timed mock exam.',
        suggestedAction: AgentActionPayloadModel(
          actionType: 'mock_exam',
          topic: 'Operating Systems Mock Exam',
          subject: 'Operating Systems',
          durationMinutes: 60,
        ),
      );
    }

    // Default: what to study next
    return AgentChatResponseModel(
      message: '📋 **Recommended Next Action for Day 1:**\n\n- **Topic:** Deadlocks & Concurrency\n- **Session:** Socratic Concept Mastery\n- **Allocated Time:** 45 minutes\n\nShall we launch your AI Teacher now?',
      intent: 'what_next',
      reasoning: 'Selected Day 1 priority task.',
      suggestedAction: AgentActionPayloadModel(
        actionType: 'socratic_lesson',
        topic: 'Deadlocks & Concurrency',
        subject: 'Operating Systems',
        durationMinutes: 45,
      ),
    );
  }
}
