class RevisionItemModel {
  final String id;
  final String topicTitle;
  final String? conceptSummary;
  final String retrievalPrompt;
  final String retrievalAnswer;
  final int intervalDays;
  final int repetitionCount;
  final double easeFactor;
  final double masteryScore;
  final double daysOverdue;
  final List<int> qualityHistory;

  RevisionItemModel({
    required this.id,
    required this.topicTitle,
    this.conceptSummary,
    required this.retrievalPrompt,
    required this.retrievalAnswer,
    required this.intervalDays,
    required this.repetitionCount,
    required this.easeFactor,
    required this.masteryScore,
    required this.daysOverdue,
    this.qualityHistory = const [],
  });

  factory RevisionItemModel.fromJson(Map<String, dynamic> json) {
    return RevisionItemModel(
      id: json['id'] as String? ?? '',
      topicTitle: json['topic_title'] as String? ?? 'General Concept',
      conceptSummary: json['concept_summary'] as String?,
      retrievalPrompt: json['retrieval_prompt'] as String? ?? '',
      retrievalAnswer: json['retrieval_answer'] as String? ?? '',
      intervalDays: json['interval_days'] as int? ?? 1,
      repetitionCount: json['repetition_count'] as int? ?? 0,
      easeFactor: (json['ease_factor'] as num?)?.toDouble() ?? 2.5,
      masteryScore: (json['mastery_score'] as num?)?.toDouble() ?? 50.0,
      daysOverdue: (json['days_overdue'] as num?)?.toDouble() ?? 0.0,
      qualityHistory: (json['quality_history'] as List<dynamic>?)?.map((e) => e as int).toList() ?? [],
    );
  }
}

class ContinueLearningInfoModel {
  final String topic;
  final String progressText;
  final String subject;

  ContinueLearningInfoModel({
    required this.topic,
    required this.progressText,
    required this.subject,
  });

  factory ContinueLearningInfoModel.fromJson(Map<String, dynamic> json) {
    return ContinueLearningInfoModel(
      topic: json['topic'] as String? ?? 'Deadlocks & Banker\'s Algorithm',
      progressText: json['progress_text'] as String? ?? 'Step 3 of 5',
      subject: json['subject'] as String? ?? 'Operating Systems',
    );
  }
}

class WeakAreaInfoModel {
  final String concept;
  final double masteryPercentage;
  final String topic;

  WeakAreaInfoModel({
    required this.concept,
    required this.masteryPercentage,
    required this.topic,
  });

  factory WeakAreaInfoModel.fromJson(Map<String, dynamic> json) {
    return WeakAreaInfoModel(
      concept: json['concept'] as String? ?? 'Circular Wait',
      masteryPercentage: (json['mastery_percentage'] as num?)?.toDouble() ?? 42.0,
      topic: json['topic'] as String? ?? 'Deadlocks',
    );
  }
}

class DailyAgendaModel {
  final ContinueLearningInfoModel continueLearning;
  final int dueForReviewCount;
  final WeakAreaInfoModel topWeakArea;
  final String recommendedAction;
  final String examPriority;
  final int reviewStreakDays;
  final double retentionRatePercentage;

  DailyAgendaModel({
    required this.continueLearning,
    required this.dueForReviewCount,
    required this.topWeakArea,
    required this.recommendedAction,
    required this.examPriority,
    required this.reviewStreakDays,
    required this.retentionRatePercentage,
  });

  factory DailyAgendaModel.fromJson(Map<String, dynamic> json) {
    return DailyAgendaModel(
      continueLearning: ContinueLearningInfoModel.fromJson(
        json['continue_learning'] as Map<String, dynamic>? ?? {},
      ),
      dueForReviewCount: json['due_for_review_count'] as int? ?? 0,
      topWeakArea: WeakAreaInfoModel.fromJson(
        json['top_weak_area'] as Map<String, dynamic>? ?? {},
      ),
      recommendedAction: json['recommended_action'] as String? ?? '5-minute active retrieval session',
      examPriority: json['exam_priority'] as String? ?? 'CPU Scheduling Algorithms',
      reviewStreakDays: json['review_streak_days'] as int? ?? 1,
      retentionRatePercentage: (json['retention_rate_percentage'] as num?)?.toDouble() ?? 85.0,
    );
  }
}

class SubmitReviewResponseModel {
  final String itemId;
  final String? topicTitle;
  final int qualityRating;
  final bool isPassed;
  final int newIntervalDays;
  final double newEaseFactor;
  final String nextReviewDate;
  final double updatedMasteryPercentage;
  final String? remediationAdvice;

  SubmitReviewResponseModel({
    required this.itemId,
    this.topicTitle,
    required this.qualityRating,
    required this.isPassed,
    required this.newIntervalDays,
    required this.newEaseFactor,
    required this.nextReviewDate,
    required this.updatedMasteryPercentage,
    this.remediationAdvice,
  });

  factory SubmitReviewResponseModel.fromJson(Map<String, dynamic> json) {
    return SubmitReviewResponseModel(
      itemId: json['item_id'] as String? ?? '',
      topicTitle: json['topic_title'] as String?,
      qualityRating: json['quality_rating'] as int? ?? 3,
      isPassed: json['is_passed'] as bool? ?? true,
      newIntervalDays: json['new_interval_days'] as int? ?? 1,
      newEaseFactor: (json['new_ease_factor'] as num?)?.toDouble() ?? 2.5,
      nextReviewDate: json['next_review_date'] as String? ?? '',
      updatedMasteryPercentage: (json['updated_mastery_percentage'] as num?)?.toDouble() ?? 70.0,
      remediationAdvice: json['remediation_advice'] as String?,
    );
  }
}
