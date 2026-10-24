class TeachingEvaluationModel {
  final String verdict;
  final String feedback;
  final bool isCorrect;
  final String? misconception;

  TeachingEvaluationModel({
    required this.verdict,
    required this.feedback,
    required this.isCorrect,
    this.misconception,
  });

  factory TeachingEvaluationModel.fromJson(Map<String, dynamic> json) {
    return TeachingEvaluationModel(
      verdict: json['verdict'] as String? ?? 'partially_correct',
      feedback: json['feedback'] as String? ?? '',
      isCorrect: json['is_correct'] as bool? ?? false,
      misconception: json['misconception'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'verdict': verdict,
      'feedback': feedback,
      'is_correct': isCorrect,
      'misconception': misconception,
    };
  }
}

class TeachingTurnModel {
  final String sessionId;
  final String state;
  final String teacherMessage;
  final String? conceptTitle;
  final String? explanation;
  final String? analogy;
  final String? checkQuestion;
  final TeachingEvaluationModel? evaluation;
  final double masteryPercentage;
  final int currentStepNumber;
  final int totalSteps;
  final bool isLessonCompleted;
  final List<String> suggestedActions;
  final Map<String, dynamic>? sourceCitation;

  TeachingTurnModel({
    required this.sessionId,
    required this.state,
    required this.teacherMessage,
    this.conceptTitle,
    this.explanation,
    this.analogy,
    this.checkQuestion,
    this.evaluation,
    required this.masteryPercentage,
    required this.currentStepNumber,
    required this.totalSteps,
    this.isLessonCompleted = false,
    this.suggestedActions = const [],
    this.sourceCitation,
  });

  factory TeachingTurnModel.fromJson(Map<String, dynamic> json) {
    TeachingEvaluationModel? eval;
    if (json['evaluation'] != null && json['evaluation'] is Map) {
      eval = TeachingEvaluationModel.fromJson(json['evaluation'] as Map<String, dynamic>);
    }

    final rawActions = json['suggested_actions'] as List<dynamic>? ?? [];

    return TeachingTurnModel(
      sessionId: json['session_id'] as String? ?? '',
      state: json['state'] as String? ?? 'assess_prior_knowledge',
      teacherMessage: json['teacher_message'] as String? ?? '',
      conceptTitle: json['concept_title'] as String?,
      explanation: json['explanation'] as String?,
      analogy: json['analogy'] as String?,
      checkQuestion: json['check_question'] as String?,
      evaluation: eval,
      masteryPercentage: (json['mastery_percentage'] as num?)?.toDouble() ?? 0.0,
      currentStepNumber: json['current_step_number'] as int? ?? 1,
      totalSteps: json['total_steps'] as int? ?? 1,
      isLessonCompleted: json['is_lesson_completed'] as bool? ?? false,
      suggestedActions: rawActions.map((e) => e.toString()).toList(),
      sourceCitation: json['source_citation'] as Map<String, dynamic>?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'state': state,
      'teacher_message': teacherMessage,
      'concept_title': conceptTitle,
      'explanation': explanation,
      'analogy': analogy,
      'check_question': checkQuestion,
      'evaluation': evaluation?.toJson(),
      'mastery_percentage': masteryPercentage,
      'current_step_number': currentStepNumber,
      'total_steps': totalSteps,
      'is_lesson_completed': isLessonCompleted,
      'suggested_actions': suggestedActions,
      'source_citation': sourceCitation,
    };
  }
}

class ActiveTeachingSessionModel {
  final String sessionId;
  final String topic;
  final String? conceptTitle;
  final int currentStepIndex;
  final int totalSteps;
  final double masteryScore;
  final DateTime updatedAt;

  ActiveTeachingSessionModel({
    required this.sessionId,
    required this.topic,
    this.conceptTitle,
    required this.currentStepIndex,
    required this.totalSteps,
    required this.masteryScore,
    required this.updatedAt,
  });

  factory ActiveTeachingSessionModel.fromJson(Map<String, dynamic> json) {
    return ActiveTeachingSessionModel(
      sessionId: json['session_id'] as String? ?? '',
      topic: json['topic'] as String? ?? '',
      conceptTitle: json['concept_title'] as String?,
      currentStepIndex: json['current_step_index'] as int? ?? 0,
      totalSteps: json['total_steps'] as int? ?? 1,
      masteryScore: (json['mastery_score'] as num?)?.toDouble() ?? 0.0,
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'topic': topic,
      'concept_title': conceptTitle,
      'current_step_index': currentStepIndex,
      'total_steps': totalSteps,
      'mastery_score': masteryScore,
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}

class TeachingSessionDetailModel {
  final String sessionId;
  final String topic;
  final String currentState;
  final int currentStepIndex;
  final double masteryScore;
  final bool isCompleted;
  final List<TeachingTurnModel> turns;

  TeachingSessionDetailModel({
    required this.sessionId,
    required this.topic,
    required this.currentState,
    required this.currentStepIndex,
    required this.masteryScore,
    required this.isCompleted,
    required this.turns,
  });

  factory TeachingSessionDetailModel.fromJson(Map<String, dynamic> json) {
    final rawTurns = json['turns'] as List<dynamic>? ?? [];
    return TeachingSessionDetailModel(
      sessionId: json['session_id'] as String? ?? '',
      topic: json['topic'] as String? ?? '',
      currentState: json['current_state'] as String? ?? '',
      currentStepIndex: json['current_step_index'] as int? ?? 0,
      masteryScore: (json['mastery_score'] as num?)?.toDouble() ?? 0.0,
      isCompleted: json['is_completed'] as bool? ?? false,
      turns: rawTurns
          .map((t) => TeachingTurnModel.fromJson(t as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'topic': topic,
      'current_state': currentState,
      'current_step_index': currentStepIndex,
      'mastery_score': masteryScore,
      'is_completed': isCompleted,
      'turns': turns.map((t) => t.toJson()).toList(),
    };
  }
}

