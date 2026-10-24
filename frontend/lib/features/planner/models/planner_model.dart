class StudyPlanModel {
  final String id;
  final String title;
  final String subject;
  final DateTime? examDate;
  final int dailyStudyMinutes;
  final int totalDays;
  final double totalAvailableHours;
  final int currentDay;
  final String status;
  final Map<String, dynamic> strategySummary;
  final DateTime? lastReplannedAt;
  final List<StudyPlanItemModel> items;
  final List<StudyPlanItemModel> todayItems;
  final double progressPercentage;

  StudyPlanModel({
    required this.id,
    required this.title,
    required this.subject,
    this.examDate,
    required this.dailyStudyMinutes,
    required this.totalDays,
    required this.totalAvailableHours,
    required this.currentDay,
    required this.status,
    this.strategySummary = const {},
    this.lastReplannedAt,
    this.items = const [],
    this.todayItems = const [],
    this.progressPercentage = 0.0,
  });

  factory StudyPlanModel.fromJson(Map<String, dynamic> json) {
    return StudyPlanModel(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? 'Study Plan',
      subject: json['subject'] as String? ?? 'Operating Systems',
      examDate: json['exam_date'] != null ? DateTime.tryParse(json['exam_date'].toString()) : null,
      dailyStudyMinutes: json['daily_study_minutes'] as int? ?? 120,
      totalDays: json['total_days'] as int? ?? 12,
      totalAvailableHours: (json['total_available_hours'] as num?)?.toDouble() ?? 24.0,
      currentDay: json['current_day'] as int? ?? 1,
      status: json['status'] as String? ?? 'active',
      strategySummary: json['strategy_summary'] as Map<String, dynamic>? ?? {},
      lastReplannedAt: json['last_replanned_at'] != null ? DateTime.tryParse(json['last_replanned_at'].toString()) : null,
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => StudyPlanItemModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      todayItems: (json['today_items'] as List<dynamic>?)
              ?.map((e) => StudyPlanItemModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      progressPercentage: (json['progress_percentage'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'subject': subject,
      'exam_date': examDate?.toIso8601String(),
      'daily_study_minutes': dailyStudyMinutes,
      'total_days': totalDays,
      'total_available_hours': totalAvailableHours,
      'current_day': currentDay,
      'status': status,
      'strategy_summary': strategySummary,
      'last_replanned_at': lastReplannedAt?.toIso8601String(),
      'items': items.map((e) => e.toJson()).toList(),
      'today_items': todayItems.map((e) => e.toJson()).toList(),
      'progress_percentage': progressPercentage,
    };
  }
}

class StudyPlanItemModel {
  final String id;
  final String planId;
  final int dayNumber;
  final DateTime? scheduledDate;
  final String sessionType; // learn, practice, revision, mock_exam, weak_repair
  final String topic;
  final int allocatedMinutes;
  final double priorityWeight;
  final String status; // pending, in_progress, completed, skipped
  final String actionType; // socratic_lesson, active_recall, practice_quiz, mock_exam
  final Map<String, dynamic> actionPayload;
  final DateTime? completedAt;
  final double? performanceScore;
  final String? notes;

  StudyPlanItemModel({
    required this.id,
    required this.planId,
    required this.dayNumber,
    this.scheduledDate,
    required this.sessionType,
    required this.topic,
    required this.allocatedMinutes,
    required this.priorityWeight,
    required this.status,
    required this.actionType,
    this.actionPayload = const {},
    this.completedAt,
    this.performanceScore,
    this.notes,
  });

  factory StudyPlanItemModel.fromJson(Map<String, dynamic> json) {
    return StudyPlanItemModel(
      id: json['id'] as String? ?? '',
      planId: json['plan_id'] as String? ?? '',
      dayNumber: json['day_number'] as int? ?? 1,
      scheduledDate: json['scheduled_date'] != null ? DateTime.tryParse(json['scheduled_date'].toString()) : null,
      sessionType: json['session_type'] as String? ?? 'learn',
      topic: json['topic'] as String? ?? 'Core Concept',
      allocatedMinutes: json['allocated_minutes'] as int? ?? 45,
      priorityWeight: (json['priority_weight'] as num?)?.toDouble() ?? 0.5,
      status: json['status'] as String? ?? 'pending',
      actionType: json['action_type'] as String? ?? 'socratic_lesson',
      actionPayload: json['action_payload'] as Map<String, dynamic>? ?? {},
      completedAt: json['completed_at'] != null ? DateTime.tryParse(json['completed_at'].toString()) : null,
      performanceScore: (json['performance_score'] as num?)?.toDouble(),
      notes: json['notes'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'plan_id': planId,
      'day_number': dayNumber,
      'scheduled_date': scheduledDate?.toIso8601String(),
      'session_type': sessionType,
      'topic': topic,
      'allocated_minutes': allocatedMinutes,
      'priority_weight': priorityWeight,
      'status': status,
      'action_type': actionType,
      'action_payload': actionPayload,
      'completed_at': completedAt?.toIso8601String(),
      'performance_score': performanceScore,
      'notes': notes,
    };
  }
}

class AgentActionPayloadModel {
  final String actionType;
  final String topic;
  final String subject;
  final int durationMinutes;
  final Map<String, dynamic> metadata;

  AgentActionPayloadModel({
    required this.actionType,
    required this.topic,
    required this.subject,
    this.durationMinutes = 30,
    this.metadata = const {},
  });

  factory AgentActionPayloadModel.fromJson(Map<String, dynamic> json) {
    return AgentActionPayloadModel(
      actionType: json['action_type'] as String? ?? 'socratic_lesson',
      topic: json['topic'] as String? ?? 'Concept',
      subject: json['subject'] as String? ?? 'Operating Systems',
      durationMinutes: json['duration_minutes'] as int? ?? 30,
      metadata: json['metadata'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'action_type': actionType,
      'topic': topic,
      'subject': subject,
      'duration_minutes': durationMinutes,
      'metadata': metadata,
    };
  }
}

class AgentChatResponseModel {
  final String message;
  final String intent;
  final String reasoning;
  final AgentActionPayloadModel? suggestedAction;
  final List<StudyPlanItemModel> todayItems;
  final Map<String, dynamic> planSummary;

  AgentChatResponseModel({
    required this.message,
    required this.intent,
    required this.reasoning,
    this.suggestedAction,
    this.todayItems = const [],
    this.planSummary = const {},
  });

  factory AgentChatResponseModel.fromJson(Map<String, dynamic> json) {
    return AgentChatResponseModel(
      message: json['message'] as String? ?? '',
      intent: json['intent'] as String? ?? 'what_next',
      reasoning: json['reasoning'] as String? ?? '',
      suggestedAction: json['suggested_action'] != null
          ? AgentActionPayloadModel.fromJson(json['suggested_action'] as Map<String, dynamic>)
          : null,
      todayItems: (json['today_items'] as List<dynamic>?)
              ?.map((e) => StudyPlanItemModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      planSummary: json['plan_summary'] as Map<String, dynamic>? ?? {},
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'intent': intent,
      'reasoning': reasoning,
      'suggested_action': suggestedAction?.toJson(),
      'today_items': todayItems.map((e) => e.toJson()).toList(),
      'plan_summary': planSummary,
    };
  }
}

class MicroSessionModel {
  final int allocatedMinutes;
  final String recommendedTopic;
  final String sessionType;
  final String actionType;
  final Map<String, dynamic> actionPayload;
  final String pedagogicalReasoning;

  MicroSessionModel({
    required this.allocatedMinutes,
    required this.recommendedTopic,
    required this.sessionType,
    required this.actionType,
    this.actionPayload = const {},
    required this.pedagogicalReasoning,
  });

  factory MicroSessionModel.fromJson(Map<String, dynamic> json) {
    return MicroSessionModel(
      allocatedMinutes: json['allocated_minutes'] as int? ?? 30,
      recommendedTopic: json['recommended_topic'] as String? ?? 'Deadlocks',
      sessionType: json['session_type'] as String? ?? 'practice',
      actionType: json['action_type'] as String? ?? 'practice_quiz',
      actionPayload: json['action_payload'] as Map<String, dynamic>? ?? {},
      pedagogicalReasoning: json['pedagogical_reasoning'] as String? ?? '',
    );
  }
}
