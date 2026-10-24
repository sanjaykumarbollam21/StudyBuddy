class QuestionModel {
  final String id;
  final int orderIndex;
  final String questionType;
  final String prompt;
  final List<String> options;
  final String difficulty;
  final String? learningObjective;
  final String? conceptTag;

  QuestionModel({
    required this.id,
    required this.orderIndex,
    required this.questionType,
    required this.prompt,
    this.options = const [],
    this.difficulty = 'medium',
    this.learningObjective,
    this.conceptTag,
  });

  factory QuestionModel.fromJson(Map<String, dynamic> json) {
    return QuestionModel(
      id: json['id'] as String? ?? '',
      orderIndex: json['order_index'] as int? ?? 1,
      questionType: json['question_type'] as String? ?? 'mcq',
      prompt: json['prompt'] as String? ?? '',
      options: (json['options'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      difficulty: json['difficulty'] as String? ?? 'medium',
      learningObjective: json['learning_objective'] as String?,
      conceptTag: json['concept_tag'] as String?,
    );
  }
}

class QuizSessionModel {
  final String sessionId;
  final String title;
  final String topic;
  final String sessionMode;
  final int totalQuestions;
  final int currentQuestionIndex;
  final String status;
  final QuestionModel? currentQuestion;

  QuizSessionModel({
    required this.sessionId,
    required this.title,
    required this.topic,
    this.sessionMode = 'practice',
    required this.totalQuestions,
    this.currentQuestionIndex = 0,
    this.status = 'in_progress',
    this.currentQuestion,
  });

  factory QuizSessionModel.fromJson(Map<String, dynamic> json) {
    return QuizSessionModel(
      sessionId: json['session_id'] as String? ?? '',
      title: json['title'] as String? ?? 'Quiz Session',
      topic: json['topic'] as String? ?? 'General',
      sessionMode: json['session_mode'] as String? ?? 'practice',
      totalQuestions: json['total_questions'] as int? ?? 5,
      currentQuestionIndex: json['current_question_index'] as int? ?? 0,
      status: json['status'] as String? ?? 'in_progress',
      currentQuestion: json['current_question'] != null
          ? QuestionModel.fromJson(json['current_question'] as Map<String, dynamic>)
          : null,
    );
  }
}

class EvaluationDetailsModel {
  final String verdict;
  final bool isCorrect;
  final double score;
  final String feedback;
  final String explanation;
  final String? misconceptionIdentified;
  final String? remediationAdvice;
  final String? conceptTag;

  EvaluationDetailsModel({
    required this.verdict,
    required this.isCorrect,
    required this.score,
    required this.feedback,
    required this.explanation,
    this.misconceptionIdentified,
    this.remediationAdvice,
    this.conceptTag,
  });

  factory EvaluationDetailsModel.fromJson(Map<String, dynamic> json) {
    return EvaluationDetailsModel(
      verdict: json['verdict'] as String? ?? 'incorrect',
      isCorrect: json['is_correct'] as bool? ?? false,
      score: (json['score'] as num?)?.toDouble() ?? 0.0,
      feedback: json['feedback'] as String? ?? '',
      explanation: json['explanation'] as String? ?? '',
      misconceptionIdentified: json['misconception_identified'] as String?,
      remediationAdvice: json['remediation_advice'] as String?,
      conceptTag: json['concept_tag'] as String?,
    );
  }
}

class SubmitAnswerResponseModel {
  final EvaluationDetailsModel evaluation;
  final double sessionScorePercentage;
  final double updatedMasteryPercentage;
  final bool isSessionCompleted;
  final int currentQuestionIndex;
  final int totalQuestions;
  final QuestionModel? nextQuestion;

  SubmitAnswerResponseModel({
    required this.evaluation,
    required this.sessionScorePercentage,
    required this.updatedMasteryPercentage,
    required this.isSessionCompleted,
    required this.currentQuestionIndex,
    required this.totalQuestions,
    this.nextQuestion,
  });

  factory SubmitAnswerResponseModel.fromJson(Map<String, dynamic> json) {
    return SubmitAnswerResponseModel(
      evaluation: EvaluationDetailsModel.fromJson(json['evaluation'] as Map<String, dynamic>),
      sessionScorePercentage: (json['session_score_percentage'] as num?)?.toDouble() ?? 0.0,
      updatedMasteryPercentage: (json['updated_mastery_percentage'] as num?)?.toDouble() ?? 0.0,
      isSessionCompleted: json['is_session_completed'] as bool? ?? false,
      currentQuestionIndex: json['current_question_index'] as int? ?? 1,
      totalQuestions: json['total_questions'] as int? ?? 5,
      nextQuestion: json['next_question'] != null
          ? QuestionModel.fromJson(json['next_question'] as Map<String, dynamic>)
          : null,
    );
  }
}

class PracticeHistoryItemModel {
  final String id;
  final String title;
  final String? topic;
  final String sessionMode;
  final int totalQuestions;
  final double scorePercentage;
  final String status;
  final String? createdAt;

  PracticeHistoryItemModel({
    required this.id,
    required this.title,
    this.topic,
    this.sessionMode = 'practice',
    required this.totalQuestions,
    required this.scorePercentage,
    required this.status,
    this.createdAt,
  });

  factory PracticeHistoryItemModel.fromJson(Map<String, dynamic> json) {
    return PracticeHistoryItemModel(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? 'Practice Session',
      topic: json['topic'] as String?,
      sessionMode: json['session_mode'] as String? ?? 'practice',
      totalQuestions: json['total_questions'] as int? ?? 0,
      scorePercentage: (json['score_percentage'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] as String? ?? 'completed',
      createdAt: json['created_at'] as String?,
    );
  }
}

class WeakAreaItemModel {
  final String topic;
  final double masteryPercentage;
  final int timesPracticed;
  final String primaryMisconception;
  final int totalMisconceptionsLogged;
  final String remediationAction;

  WeakAreaItemModel({
    required this.topic,
    required this.masteryPercentage,
    required this.timesPracticed,
    required this.primaryMisconception,
    required this.totalMisconceptionsLogged,
    required this.remediationAction,
  });

  factory WeakAreaItemModel.fromJson(Map<String, dynamic> json) {
    return WeakAreaItemModel(
      topic: json['topic'] as String? ?? 'General Topic',
      masteryPercentage: (json['mastery_percentage'] as num?)?.toDouble() ?? 0.0,
      timesPracticed: json['times_practiced'] as int? ?? 0,
      primaryMisconception: json['primary_misconception'] as String? ?? 'Conceptual gap detected.',
      totalMisconceptionsLogged: json['total_misconceptions_logged'] as int? ?? 1,
      remediationAction: json['remediation_action'] as String? ?? 'Review with Socratic AI Teacher',
    );
  }
}
