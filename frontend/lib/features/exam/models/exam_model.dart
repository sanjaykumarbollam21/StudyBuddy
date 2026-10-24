class ExamConfigModel {
  final String id;
  final String title;
  final String subject;
  final int totalMarks;
  final int durationMinutes;
  final double passingPercentage;
  final double negativeMarkingRatio;
  final Map<String, double> blueprint;
  final DateTime? examDate;

  ExamConfigModel({
    required this.id,
    required this.title,
    required this.subject,
    this.totalMarks = 100,
    this.durationMinutes = 60,
    this.passingPercentage = 40.0,
    this.negativeMarkingRatio = 0.25,
    this.blueprint = const {},
    this.examDate,
  });

  factory ExamConfigModel.fromJson(Map<String, dynamic> json) {
    return ExamConfigModel(
      id: json['id'] as String? ?? 'cfg-default',
      title: json['title'] as String? ?? 'Semester Exam',
      subject: json['subject'] as String? ?? 'Operating Systems',
      totalMarks: (json['total_marks'] as num?)?.toInt() ?? 100,
      durationMinutes: (json['duration_minutes'] as num?)?.toInt() ?? 60,
      passingPercentage: (json['passing_percentage'] as num?)?.toDouble() ?? 40.0,
      negativeMarkingRatio: (json['negative_marking_ratio'] as num?)?.toDouble() ?? 0.25,
      blueprint: (json['blueprint'] as Map<String, dynamic>?)?.map(
            (k, v) => MapEntry(k, (v as num).toDouble()),
          ) ??
          {},
      examDate: json['exam_date'] != null ? DateTime.tryParse(json['exam_date'] as String) : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'subject': subject,
      'total_marks': totalMarks,
      'duration_minutes': durationMinutes,
      'passing_percentage': passingPercentage,
      'negative_marking_ratio': negativeMarkingRatio,
      'blueprint': blueprint,
      'exam_date': examDate?.toIso8601String(),
    };
  }
}

class MockExamQuestionModel {
  final String id;
  final String topic;
  final String questionType;
  final String prompt;
  final List<String> options;
  final double marks;
  final double negativeMarks;
  final int orderIndex;
  final String difficulty;
  final String? conceptTag;
  final String? learningObjective;

  MockExamQuestionModel({
    required this.id,
    required this.topic,
    required this.questionType,
    required this.prompt,
    required this.options,
    this.marks = 10.0,
    this.negativeMarks = 2.5,
    this.orderIndex = 1,
    this.difficulty = 'intermediate',
    this.conceptTag,
    this.learningObjective,
  });

  factory MockExamQuestionModel.fromJson(Map<String, dynamic> json) {
    return MockExamQuestionModel(
      id: json['id'] as String? ?? 'q-unknown',
      topic: json['topic'] as String? ?? 'General',
      questionType: json['question_type'] as String? ?? 'mcq',
      prompt: json['prompt'] as String? ?? '',
      options: (json['options'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      marks: (json['marks'] as num?)?.toDouble() ?? 10.0,
      negativeMarks: (json['negative_marks'] as num?)?.toDouble() ?? 2.5,
      orderIndex: (json['order_index'] as num?)?.toInt() ?? 1,
      difficulty: json['difficulty'] as String? ?? 'intermediate',
      conceptTag: json['concept_tag'] as String?,
      learningObjective: json['learning_objective'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'topic': topic,
      'question_type': questionType,
      'prompt': prompt,
      'options': options,
      'marks': marks,
      'negative_marks': negativeMarks,
      'order_index': orderIndex,
      'difficulty': difficulty,
      'concept_tag': conceptTag,
      'learning_objective': learningObjective,
    };
  }
}

class MockExamSessionModel {
  final String id;
  final String? examConfigId;
  final String title;
  final String subject;
  final int durationMinutes;
  final int timeRemainingSeconds;
  final String status;
  final int totalQuestions;
  final double totalMarks;
  final List<MockExamQuestionModel> questions;
  final List<String> reviewFlags;
  final Map<String, dynamic> answersRecord;

  MockExamSessionModel({
    required this.id,
    this.examConfigId,
    required this.title,
    required this.subject,
    this.durationMinutes = 60,
    this.timeRemainingSeconds = 3600,
    this.status = 'in_progress',
    this.totalQuestions = 10,
    this.totalMarks = 100.0,
    required this.questions,
    this.reviewFlags = const [],
    this.answersRecord = const {},
  });

  factory MockExamSessionModel.fromJson(Map<String, dynamic> json) {
    return MockExamSessionModel(
      id: json['id'] as String? ?? 'session-default',
      examConfigId: json['exam_config_id'] as String?,
      title: json['title'] as String? ?? 'Mock Exam',
      subject: json['subject'] as String? ?? 'Operating Systems',
      durationMinutes: (json['duration_minutes'] as num?)?.toInt() ?? 60,
      timeRemainingSeconds: (json['time_remaining_seconds'] as num?)?.toInt() ?? 3600,
      status: json['status'] as String? ?? 'in_progress',
      totalQuestions: (json['total_questions'] as num?)?.toInt() ?? 10,
      totalMarks: (json['total_marks'] as num?)?.toDouble() ?? 100.0,
      questions: (json['questions'] as List<dynamic>?)
              ?.map((q) => MockExamQuestionModel.fromJson(q as Map<String, dynamic>))
              .toList() ??
          [],
      reviewFlags: (json['review_flags'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      answersRecord: (json['answers_record'] as Map<String, dynamic>?) ?? {},
    );
  }
}

class TopicPerformanceModel {
  final String topic;
  final double scorePercentage;
  final String tier; // Strong, Good, Weak, Critical
  final int correctCount;
  final int questionCount;
  final double marksObtained;
  final double totalMarks;

  TopicPerformanceModel({
    required this.topic,
    required this.scorePercentage,
    required this.tier,
    required this.correctCount,
    required this.questionCount,
    required this.marksObtained,
    required this.totalMarks,
  });

  factory TopicPerformanceModel.fromJson(Map<String, dynamic> json) {
    return TopicPerformanceModel(
      topic: json['topic'] as String? ?? '',
      scorePercentage: (json['score_percentage'] as num?)?.toDouble() ?? 0.0,
      tier: json['tier'] as String? ?? 'Good',
      correctCount: (json['correct_count'] as num?)?.toInt() ?? 0,
      questionCount: (json['question_count'] as num?)?.toInt() ?? 0,
      marksObtained: (json['marks_obtained'] as num?)?.toDouble() ?? 0.0,
      totalMarks: (json['total_marks'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class CognitiveDiagnosisModel {
  final String coreIssue;
  final String deepExplanation;
  final String keyRemediationConcept;
  final int detectedMisconceptionsCount;
  final int unansweredQuestions;

  CognitiveDiagnosisModel({
    required this.coreIssue,
    required this.deepExplanation,
    required this.keyRemediationConcept,
    this.detectedMisconceptionsCount = 0,
    this.unansweredQuestions = 0,
  });

  factory CognitiveDiagnosisModel.fromJson(Map<String, dynamic> json) {
    return CognitiveDiagnosisModel(
      coreIssue: json['core_issue'] as String? ?? 'Diagnosis completed.',
      deepExplanation: json['deep_explanation'] as String? ?? '',
      keyRemediationConcept: json['key_remediation_concept'] as String? ?? '',
      detectedMisconceptionsCount: (json['detected_misconceptions_count'] as num?)?.toInt() ?? 0,
      unansweredQuestions: (json['unanswered_questions'] as num?)?.toInt() ?? 0,
    );
  }
}

class RemediationActionModel {
  final String targetTopic;
  final String ctaTitle;
  final String prompt;
  final String learningObjective;

  RemediationActionModel({
    required this.targetTopic,
    required this.ctaTitle,
    required this.prompt,
    required this.learningObjective,
  });

  factory RemediationActionModel.fromJson(Map<String, dynamic> json) {
    return RemediationActionModel(
      targetTopic: json['target_topic'] as String? ?? 'Deadlocks',
      ctaTitle: json['cta_title'] as String? ?? 'Reteach Deadlocks',
      prompt: json['prompt'] as String? ?? '',
      learningObjective: json['learning_objective'] as String? ?? '',
    );
  }
}

class ExamReadinessDetailModel {
  final double readinessPercentage;
  final String readinessCategory;
  final String readinessMessage;
  final String actionableProjection;
  final Map<String, double> dimensionScores;
  final List<String> strongTopics;
  final List<String> weakTopics;
  final List<String> criticalTopics;

  ExamReadinessDetailModel({
    required this.readinessPercentage,
    required this.readinessCategory,
    required this.readinessMessage,
    required this.actionableProjection,
    this.dimensionScores = const {},
    this.strongTopics = const [],
    this.weakTopics = const [],
    this.criticalTopics = const [],
  });

  factory ExamReadinessDetailModel.fromJson(Map<String, dynamic> json) {
    return ExamReadinessDetailModel(
      readinessPercentage: (json['readiness_percentage'] as num?)?.toDouble() ?? 65.0,
      readinessCategory: json['readiness_category'] as String? ?? 'Moderate Exam Readiness',
      readinessMessage: json['readiness_message'] as String? ?? '',
      actionableProjection: json['actionable_projection'] as String? ?? '',
      dimensionScores: (json['dimension_scores'] as Map<String, dynamic>?)?.map(
            (k, v) => MapEntry(k, (v as num).toDouble()),
          ) ??
          {},
      strongTopics: (json['strong_topics'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      weakTopics: (json['weak_topics'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      criticalTopics: (json['critical_topics'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class ExamResultModel {
  final String id;
  final String title;
  final String status;
  final double scorePercentage;
  final double marksObtained;
  final double totalMarks;
  final double negativeMarksDeducted;
  final int correctCount;
  final int incorrectCount;
  final int unansweredCount;
  final List<TopicPerformanceModel> topicAnalysis;
  final CognitiveDiagnosisModel cognitiveDiagnosis;
  final RemediationActionModel remediationAction;
  final ExamReadinessDetailModel readiness;

  ExamResultModel({
    required this.id,
    required this.title,
    required this.status,
    required this.scorePercentage,
    required this.marksObtained,
    required this.totalMarks,
    required this.negativeMarksDeducted,
    required this.correctCount,
    required this.incorrectCount,
    required this.unansweredCount,
    required this.topicAnalysis,
    required this.cognitiveDiagnosis,
    required this.remediationAction,
    required this.readiness,
  });

  factory ExamResultModel.fromJson(Map<String, dynamic> json) {
    return ExamResultModel(
      id: json['id'] as String? ?? '',
      title: json['title'] as String? ?? 'Exam Results',
      status: json['status'] as String? ?? 'submitted',
      scorePercentage: (json['score_percentage'] as num?)?.toDouble() ?? 0.0,
      marksObtained: (json['marks_obtained'] as num?)?.toDouble() ?? 0.0,
      totalMarks: (json['total_marks'] as num?)?.toDouble() ?? 100.0,
      negativeMarksDeducted: (json['negative_marks_deducted'] as num?)?.toDouble() ?? 0.0,
      correctCount: (json['correct_count'] as num?)?.toInt() ?? 0,
      incorrectCount: (json['incorrect_count'] as num?)?.toInt() ?? 0,
      unansweredCount: (json['unanswered_count'] as num?)?.toInt() ?? 0,
      topicAnalysis: (json['topic_analysis'] as List<dynamic>?)
              ?.map((t) => TopicPerformanceModel.fromJson(t as Map<String, dynamic>))
              .toList() ??
          [],
      cognitiveDiagnosis: CognitiveDiagnosisModel.fromJson(
        (json['cognitive_diagnosis'] as Map<String, dynamic>?) ?? {},
      ),
      remediationAction: RemediationActionModel.fromJson(
        (json['remediation_action'] as Map<String, dynamic>?) ?? {},
      ),
      readiness: ExamReadinessDetailModel.fromJson(
        (json['readiness'] as Map<String, dynamic>?) ?? {},
      ),
    );
  }
}
