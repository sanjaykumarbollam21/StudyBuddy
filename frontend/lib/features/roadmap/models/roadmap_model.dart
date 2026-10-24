class RoadmapTopicModel {
  final String? id;
  final int orderIndex;
  final String customTitle;
  final String? description;
  final String difficulty;
  final int estimatedMinutes;
  final String status; // locked, unlocked, in_progress, mastered
  final double masteryScore;
  final List<String> prerequisites;
  final List<String> subConcepts;
  final List<String> learningObjectives;

  RoadmapTopicModel({
    this.id,
    required this.orderIndex,
    required this.customTitle,
    this.description,
    this.difficulty = 'medium',
    this.estimatedMinutes = 30,
    required this.status,
    this.masteryScore = 0.0,
    this.prerequisites = const [],
    this.subConcepts = const [],
    this.learningObjectives = const [],
  });

  bool get isLocked => status == 'locked';
  bool get isInProgress => status == 'in_progress';
  bool get isMastered => status == 'mastered';
  bool get isUnlocked => status == 'unlocked' || status == 'in_progress';

  factory RoadmapTopicModel.fromJson(Map<String, dynamic> json) {
    return RoadmapTopicModel(
      id: json['id'] as String?,
      orderIndex: json['order_index'] as int? ?? 1,
      customTitle: json['custom_title'] as String? ?? 'Untitled Topic',
      description: json['description'] as String?,
      difficulty: json['difficulty'] as String? ?? 'medium',
      estimatedMinutes: json['estimated_minutes'] as int? ?? 30,
      status: json['status'] as String? ?? 'locked',
      masteryScore: (json['mastery_score'] as num?)?.toDouble() ?? 0.0,
      prerequisites: (json['prerequisites'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      subConcepts: (json['sub_concepts'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      learningObjectives: (json['learning_objectives'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

class RoadmapModel {
  final String id;
  final String title;
  final String? subject;
  final String? goal;
  final String sourceType;
  final int totalSteps;
  final int completedSteps;
  final double progressPercentage;
  final String status;
  final List<RoadmapTopicModel> topics;

  RoadmapModel({
    required this.id,
    required this.title,
    this.subject,
    this.goal,
    this.sourceType = 'foundational',
    required this.totalSteps,
    required this.completedSteps,
    required this.progressPercentage,
    required this.status,
    required this.topics,
  });

  factory RoadmapModel.fromJson(Map<String, dynamic> json) {
    return RoadmapModel(
      id: json['id'] as String? ?? 'lp-1',
      title: json['title'] as String? ?? 'Learning Roadmap',
      subject: json['subject'] as String?,
      goal: json['goal'] as String?,
      sourceType: json['source_type'] as String? ?? 'foundational',
      totalSteps: json['total_steps'] as int? ?? 0,
      completedSteps: json['completed_steps'] as int? ?? 0,
      progressPercentage: (json['progress_percentage'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] as String? ?? 'in_progress',
      topics: (json['topics'] as List<dynamic>?)
              ?.map((t) => RoadmapTopicModel.fromJson(t as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}

class NextRecommendationModel {
  final String roadmapId;
  final String roadmapTitle;
  final String topicTitle;
  final String description;
  final String difficulty;
  final int estimatedMinutes;
  final String status;
  final List<String> prerequisites;
  final List<String> learningObjectives;
  final String whyRecommended;

  NextRecommendationModel({
    required this.roadmapId,
    required this.roadmapTitle,
    required this.topicTitle,
    required this.description,
    this.difficulty = 'medium',
    this.estimatedMinutes = 30,
    required this.status,
    this.prerequisites = const [],
    this.learningObjectives = const [],
    required this.whyRecommended,
  });

  factory NextRecommendationModel.fromJson(Map<String, dynamic> json) {
    return NextRecommendationModel(
      roadmapId: json['roadmap_id'] as String? ?? '',
      roadmapTitle: json['roadmap_title'] as String? ?? 'Curriculum',
      topicTitle: json['topic_title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      difficulty: json['difficulty'] as String? ?? 'medium',
      estimatedMinutes: json['estimated_minutes'] as int? ?? 30,
      status: json['status'] as String? ?? 'in_progress',
      prerequisites: (json['prerequisites'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      learningObjectives: (json['learning_objectives'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      whyRecommended: json['why_recommended'] as String? ?? 'Recommended based on your curriculum roadmap.',
    );
  }
}

class WhyLearningModel {
  final String topicTitle;
  final List<String> prerequisites;
  final List<String> unlockedNext;
  final String fullExplanation;
  final String coreValue;
  final String prerequisiteConnection;
  final String futureUnlocks;

  WhyLearningModel({
    required this.topicTitle,
    this.prerequisites = const [],
    this.unlockedNext = const [],
    required this.fullExplanation,
    required this.coreValue,
    required this.prerequisiteConnection,
    required this.futureUnlocks,
  });

  factory WhyLearningModel.fromJson(Map<String, dynamic> json) {
    return WhyLearningModel(
      topicTitle: json['topic_title'] as String? ?? '',
      prerequisites: (json['prerequisites'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      unlockedNext: (json['unlocked_next'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      fullExplanation: json['full_explanation'] as String? ?? '',
      coreValue: json['core_value'] as String? ?? '',
      prerequisiteConnection: json['prerequisite_connection'] as String? ?? '',
      futureUnlocks: json['future_unlocks'] as String? ?? '',
    );
  }
}
