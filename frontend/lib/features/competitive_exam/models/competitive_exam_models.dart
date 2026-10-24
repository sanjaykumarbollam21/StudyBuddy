class CompetitiveExamProfileModel {
  final String id;
  final String examId;
  final String examName;
  final int targetYear;
  final String? targetDate;
  final String currentStage;
  final String? optionalSubject;
  final double dailyTargetHours;
  final String language;
  final Map<String, dynamic> dafDetails;

  CompetitiveExamProfileModel({
    required this.id,
    required this.examId,
    required this.examName,
    required this.targetYear,
    this.targetDate,
    required this.currentStage,
    this.optionalSubject,
    required this.dailyTargetHours,
    required this.language,
    required this.dafDetails,
  });

  factory CompetitiveExamProfileModel.fromJson(Map<String, dynamic> json) {
    return CompetitiveExamProfileModel(
      id: json['id'] as String? ?? 'default-profile',
      examId: json['exam_id'] as String? ?? 'upsc_cse',
      examName: json['exam_name'] as String? ?? 'UPSC Civil Services Examination',
      targetYear: (json['target_year'] as num?)?.toInt() ?? 2027,
      targetDate: json['target_date'] as String?,
      currentStage: json['current_stage'] as String? ?? 'prelims',
      optionalSubject: json['optional_subject'] as String?,
      dailyTargetHours: (json['daily_target_hours'] as num?)?.toDouble() ?? 6.0,
      language: json['language'] as String? ?? 'English',
      dafDetails: json['daf_details'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(json['daf_details'] as Map)
          : <String, dynamic>{},
    );
  }
}

class ExamDefinitionModel {
  final String id;
  final String name;
  final String category;
  final String conductingBody;
  final List<String> stages;
  final List<String> subjects;
  final bool hasNegativeMarking;
  final double defaultDailyHours;

  ExamDefinitionModel({
    required this.id,
    required this.name,
    required this.category,
    required this.conductingBody,
    required this.stages,
    required this.subjects,
    required this.hasNegativeMarking,
    required this.defaultDailyHours,
  });

  factory ExamDefinitionModel.fromJson(Map<String, dynamic> json) {
    return ExamDefinitionModel(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      category: json['category'] as String? ?? '',
      conductingBody: json['conducting_body'] as String? ?? '',
      stages: (json['stages'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      subjects: (json['subjects'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      hasNegativeMarking: json['has_negative_marking'] as bool? ?? true,
      defaultDailyHours: (json['default_daily_hours'] as num?)?.toDouble() ?? 5.0,
    );
  }
}

class PYQModel {
  final String id;
  final String examId;
  final int year;
  final String stage;
  final String paperName;
  final String topicTitle;
  final String? subtopicTitle;
  final String questionText;
  final String questionType;
  final List<PYQOptionModel> options;
  final String correctAnswer;
  final String explanation;
  final double marks;
  final double negativeMarks;
  final String difficulty;
  final String? examTrendNote;
  final String? sourceCitation;

  PYQModel({
    required this.id,
    required this.examId,
    required this.year,
    required this.stage,
    required this.paperName,
    required this.topicTitle,
    this.subtopicTitle,
    required this.questionText,
    required this.questionType,
    required this.options,
    required this.correctAnswer,
    required this.explanation,
    required this.marks,
    required this.negativeMarks,
    required this.difficulty,
    this.examTrendNote,
    this.sourceCitation,
  });

  factory PYQModel.fromJson(Map<String, dynamic> json) {
    return PYQModel(
      id: json['id'] as String? ?? '',
      examId: json['exam_id'] as String? ?? 'upsc_cse',
      year: (json['year'] as num?)?.toInt() ?? 2024,
      stage: json['stage'] as String? ?? 'prelims',
      paperName: json['paper_name'] as String? ?? '',
      topicTitle: json['topic_title'] as String? ?? '',
      subtopicTitle: json['subtopic_title'] as String?,
      questionText: json['question_text'] as String? ?? '',
      questionType: json['question_type'] as String? ?? 'single_correct',
      options: (json['options'] as List<dynamic>?)
              ?.map((o) => PYQOptionModel.fromJson(o as Map<String, dynamic>))
              .toList() ??
          [],
      correctAnswer: json['correct_answer'] as String? ?? 'A',
      explanation: json['explanation'] as String? ?? '',
      marks: (json['marks'] as num?)?.toDouble() ?? 2.0,
      negativeMarks: (json['negative_marks'] as num?)?.toDouble() ?? 0.66,
      difficulty: json['difficulty'] as String? ?? 'medium',
      examTrendNote: json['exam_trend_note'] as String?,
      sourceCitation: json['source_citation'] as String?,
    );
  }
}

class PYQOptionModel {
  final String label;
  final String text;

  PYQOptionModel({required this.label, required this.text});

  factory PYQOptionModel.fromJson(Map<String, dynamic> json) {
    return PYQOptionModel(
      label: json['label'] as String? ?? '',
      text: json['text'] as String? ?? '',
    );
  }
}

class PYQAttemptResultModel {
  final String id;
  final bool isCorrect;
  final double marksAwarded;
  final String? errorType;
  final String explanation;
  final String? examTrendNote;
  final String? sourceCitation;

  PYQAttemptResultModel({
    required this.id,
    required this.isCorrect,
    required this.marksAwarded,
    this.errorType,
    required this.explanation,
    this.examTrendNote,
    this.sourceCitation,
  });

  factory PYQAttemptResultModel.fromJson(Map<String, dynamic> json) {
    return PYQAttemptResultModel(
      id: json['id'] as String? ?? '',
      isCorrect: json['is_correct'] as bool? ?? false,
      marksAwarded: (json['marks_awarded'] as num?)?.toDouble() ?? 0.0,
      errorType: json['error_type'] as String?,
      explanation: json['explanation'] as String? ?? '',
      examTrendNote: json['exam_trend_note'] as String?,
      sourceCitation: json['source_citation'] as String?,
    );
  }
}

class CurrentAffairModel {
  final String id;
  final String date;
  final String title;
  final String category;
  final String summary;
  final String background;
  final List<StaticConceptLinkModel> staticConcepts;
  final List<String> prelimsPointers;
  final List<String> mainsPointers;
  final String source;

  CurrentAffairModel({
    required this.id,
    required this.date,
    required this.title,
    required this.category,
    required this.summary,
    required this.background,
    required this.staticConcepts,
    required this.prelimsPointers,
    required this.mainsPointers,
    required this.source,
  });

  factory CurrentAffairModel.fromJson(Map<String, dynamic> json) {
    return CurrentAffairModel(
      id: json['id'] as String? ?? '',
      date: json['date'] as String? ?? '',
      title: json['title'] as String? ?? '',
      category: json['category'] as String? ?? 'General',
      summary: json['summary'] as String? ?? '',
      background: json['background'] as String? ?? '',
      staticConcepts: (json['static_concepts'] as List<dynamic>?)
              ?.map((c) => StaticConceptLinkModel.fromJson(c as Map<String, dynamic>))
              .toList() ??
          [],
      prelimsPointers: (json['prelims_pointers'] as List<dynamic>?)?.map((p) => p.toString()).toList() ?? [],
      mainsPointers: (json['mains_pointers'] as List<dynamic>?)?.map((p) => p.toString()).toList() ?? [],
      source: json['source'] as String? ?? '',
    );
  }
}

class StaticConceptLinkModel {
  final String concept;
  final String description;

  StaticConceptLinkModel({required this.concept, required this.description});

  factory StaticConceptLinkModel.fromJson(Map<String, dynamic> json) {
    return StaticConceptLinkModel(
      concept: json['concept'] as String? ?? '',
      description: json['description'] as String? ?? '',
    );
  }
}

class MainsAnswerEvaluationModel {
  final int wordCount;
  final int wordLimit;
  final double totalMarks;
  final double marksObtained;
  final double scorePercentage;
  final Map<String, double> rubricBreakdown;
  final List<String> strengths;
  final List<String> missingDimensions;
  final String improvementGuidelines;
  final String modelOutline;
  final String paperName;

  MainsAnswerEvaluationModel({
    required this.wordCount,
    required this.wordLimit,
    required this.totalMarks,
    required this.marksObtained,
    required this.scorePercentage,
    required this.rubricBreakdown,
    required this.strengths,
    required this.missingDimensions,
    required this.improvementGuidelines,
    required this.modelOutline,
    required this.paperName,
  });

  factory MainsAnswerEvaluationModel.fromJson(Map<String, dynamic> json) {
    final rubrics = <String, double>{};
    if (json['rubric_breakdown'] is Map) {
      (json['rubric_breakdown'] as Map).forEach((k, v) {
        rubrics[k.toString()] = (v as num?)?.toDouble() ?? 0.0;
      });
    }

    return MainsAnswerEvaluationModel(
      wordCount: (json['word_count'] as num?)?.toInt() ?? 0,
      wordLimit: (json['word_limit'] as num?)?.toInt() ?? 150,
      totalMarks: (json['total_marks'] as num?)?.toDouble() ?? 10.0,
      marksObtained: (json['marks_obtained'] as num?)?.toDouble() ?? 0.0,
      scorePercentage: (json['score_percentage'] as num?)?.toDouble() ?? 0.0,
      rubricBreakdown: rubrics,
      strengths: (json['strengths'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      missingDimensions: (json['missing_dimensions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      improvementGuidelines: json['improvement_guidelines'] as String? ?? '',
      modelOutline: json['model_outline'] as String? ?? '',
      paperName: json['paper_name'] as String? ?? '',
    );
  }
}

class ReadinessReportModel {
  final String examId;
  final String examName;
  final int targetYear;
  final int daysRemaining;
  final double overallPreparationPercentage;
  final Map<String, double> readinessRadar;
  final Map<String, dynamic> todayPriority;
  final Map<String, dynamic> topicHeatmap;

  ReadinessReportModel({
    required this.examId,
    required this.examName,
    required this.targetYear,
    required this.daysRemaining,
    required this.overallPreparationPercentage,
    required this.readinessRadar,
    required this.todayPriority,
    required this.topicHeatmap,
  });

  factory ReadinessReportModel.fromJson(Map<String, dynamic> json) {
    final radar = <String, double>{};
    final rawRadar = json['readiness_radar'] ?? json['readiness_index'];
    if (rawRadar is Map) {
      rawRadar.forEach((k, v) {
        radar[k.toString()] = (v as num?)?.toDouble() ?? 0.0;
      });
    }

    return ReadinessReportModel(
      examId: json['exam_id'] as String? ?? 'upsc_cse',
      examName: json['exam_name'] as String? ?? 'UPSC CSE',
      targetYear: (json['target_year'] as num?)?.toInt() ?? 2027,
      daysRemaining: (json['days_remaining'] as num?)?.toInt() ?? 120,
      overallPreparationPercentage: (json['overall_preparation_percentage'] as num?)?.toDouble() ?? 50.0,
      readinessRadar: radar,
      todayPriority: json['today_priority'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(json['today_priority'] as Map)
          : <String, dynamic>{},
      topicHeatmap: json['topic_heatmap'] is Map<String, dynamic>
          ? Map<String, dynamic>.from(json['topic_heatmap'] as Map)
          : <String, dynamic>{},
    );
  }
}
