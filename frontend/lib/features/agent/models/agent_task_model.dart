class AgentActionStepModel {
  final int step;
  final String type;
  final String topic;
  final int durationMins;
  final String engine;
  final String description;
  final Map<String, dynamic> payload;

  AgentActionStepModel({
    required this.step,
    required this.type,
    required this.topic,
    required this.durationMins,
    required this.engine,
    required this.description,
    this.payload = const {},
  });

  factory AgentActionStepModel.fromJson(Map<String, dynamic> json) => AgentActionStepModel(
    step: json['step'] as int? ?? 1,
    type: json['type'] as String? ?? 'learn',
    topic: json['topic'] as String? ?? '',
    durationMins: json['duration_mins'] as int? ?? 15,
    engine: json['engine'] as String? ?? 'TeacherEngine',
    description: json['description'] as String? ?? '',
    payload: json['payload'] as Map<String, dynamic>? ?? {},
  );

  Map<String, dynamic> toJson() => {
    'step': step,
    'type': type,
    'topic': topic,
    'duration_mins': durationMins,
    'engine': engine,
    'description': description,
    'payload': payload,
  };
}

class AgentTaskModel {
  final String id;
  final String userId;
  final String goal;
  final String reason;
  final String priority;
  final String permissionLevel;
  String currentState;
  final List<AgentActionStepModel> proposedActions;
  Map<String, dynamic> executionResult;
  final Map<String, dynamic> explanationBreakdown;
  final int allocatedMinutes;
  int currentStepIndex;
  Map<String, dynamic> stepProgress;
  final bool isResumable;
  final DateTime? createdAt;
  final DateTime? completedAt;
  final DateTime? interruptedAt;

  AgentTaskModel({
    required this.id,
    required this.userId,
    required this.goal,
    required this.reason,
    required this.priority,
    required this.permissionLevel,
    required this.currentState,
    required this.proposedActions,
    this.executionResult = const {},
    this.explanationBreakdown = const {},
    required this.allocatedMinutes,
    this.currentStepIndex = 0,
    this.stepProgress = const {},
    this.isResumable = true,
    this.createdAt,
    this.completedAt,
    this.interruptedAt,
  });

  factory AgentTaskModel.fromJson(Map<String, dynamic> json) => AgentTaskModel(
    id: json['id'] as String,
    userId: json['user_id'] as String? ?? 'user-current',
    goal: json['goal'] as String? ?? 'Prepare topic',
    reason: json['reason'] as String? ?? '',
    priority: json['priority'] as String? ?? 'high',
    permissionLevel: json['permission_level'] as String? ?? 'requires_permission',
    currentState: json['current_state'] as String? ?? 'proposed',
    proposedActions: (json['proposed_actions'] as List<dynamic>? ?? [])
        .map((a) => AgentActionStepModel.fromJson(a as Map<String, dynamic>))
        .toList(),
    executionResult: json['execution_result'] as Map<String, dynamic>? ?? {},
    explanationBreakdown: json['explanation_breakdown'] as Map<String, dynamic>? ?? {},
    allocatedMinutes: json['allocated_minutes'] as int? ?? 45,
    currentStepIndex: json['current_step_index'] as int? ?? 0,
    stepProgress: json['step_progress'] as Map<String, dynamic>? ?? {},
    isResumable: json['is_resumable'] as bool? ?? true,
    createdAt: json['created_at'] != null ? DateTime.parse(json['created_at'] as String) : null,
    completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at'] as String) : null,
    interruptedAt: json['interrupted_at'] != null ? DateTime.parse(json['interrupted_at'] as String) : null,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'user_id': userId,
    'goal': goal,
    'reason': reason,
    'priority': priority,
    'permission_level': permissionLevel,
    'current_state': currentState,
    'proposed_actions': proposedActions.map((a) => a.toJson()).toList(),
    'execution_result': executionResult,
    'explanation_breakdown': explanationBreakdown,
    'allocated_minutes': allocatedMinutes,
    'current_step_index': currentStepIndex,
    'step_progress': stepProgress,
    'is_resumable': isResumable,
    'created_at': createdAt?.toIso8601String(),
    'completed_at': completedAt?.toIso8601String(),
    'interrupted_at': interruptedAt?.toIso8601String(),
  };
}

class AgentChatResponseModel {
  final String reply;
  final String intentDetected;
  final AgentTaskModel? suggestedTask;
  final List<String> orchestratedEngines;
  final Map<String, dynamic> explainability;

  AgentChatResponseModel({
    required this.reply,
    required this.intentDetected,
    this.suggestedTask,
    this.orchestratedEngines = const [],
    this.explainability = const {},
  });

  factory AgentChatResponseModel.fromJson(Map<String, dynamic> json) => AgentChatResponseModel(
    reply: json['reply'] as String? ?? '',
    intentDetected: json['intent_detected'] as String? ?? '',
    suggestedTask: json['suggested_task'] != null
        ? AgentTaskModel.fromJson(json['suggested_task'] as Map<String, dynamic>)
        : null,
    orchestratedEngines: (json['orchestrated_engines'] as List<dynamic>? ?? []).map((e) => e.toString()).toList(),
    explainability: json['explainability'] as Map<String, dynamic>? ?? {},
  );
}
