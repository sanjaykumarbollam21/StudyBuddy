import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/storage/offline_storage_service.dart';
import '../models/roadmap_model.dart';

class RoadmapApiService {
  final ApiClient _client = ApiClient();

  Future<RoadmapModel> generateRoadmap({
    required String subject,
    String? goal,
    String? documentId,
  }) async {
    final body = <String, dynamic>{
      'subject': subject,
    };
    if (goal != null) body['goal'] = goal;
    if (documentId != null) body['document_id'] = documentId;

    try {
      final response = await _client.post(
        '${AppConfig.baseUrl}/curriculum/roadmap/generate',
        body: body,
      );
      return RoadmapModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      return _getOfflineFallbackRoadmap(subject, goal);
    }
  }

  Future<RoadmapModel> getRoadmap(String roadmapId) async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/curriculum/roadmap/$roadmapId');
      return RoadmapModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      return _getOfflineFallbackRoadmap('Operating Systems', null);
    }
  }

  Future<NextRecommendationModel> getNextRecommendation({String? roadmapId}) async {
    try {
      final query = roadmapId != null ? '?roadmap_id=$roadmapId' : '';
      final response = await _client.get('${AppConfig.baseUrl}/curriculum/next$query');
      return NextRecommendationModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      return NextRecommendationModel(
        roadmapId: 'offline-lp',
        roadmapTitle: 'Operating Systems Mastery Track',
        topicTitle: 'OS Fundamentals & Architecture',
        description: 'Role of the operating system, kernel vs user mode, system calls, and hardware abstraction.',
        difficulty: 'beginner',
        estimatedMinutes: 30,
        status: 'in_progress',
        prerequisites: const [],
        learningObjectives: const [
          'Understand user mode vs kernel mode privilege rings',
          'Explain traps, interrupts, and system call interface',
        ],
        whyRecommended: 'Foundational starting point with no prerequisites required.',
      );
    }
  }

  Future<WhyLearningModel> getWhyLearning({
    required String topic,
    String? roadmapId,
    String? goal,
  }) async {
    try {
      final queryParams = <String, String>{
        'topic': topic,
      };
      if (roadmapId != null) queryParams['roadmap_id'] = roadmapId;
      if (goal != null) queryParams['goal'] = goal;
      final uri = Uri.parse('${AppConfig.baseUrl}/curriculum/why').replace(queryParameters: queryParams);
      final response = await _client.get(uri.toString());
      return WhyLearningModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      return WhyLearningModel(
        topicTitle: topic,
        prerequisites: const ['Foundational Concepts'],
        unlockedNext: const ['Advanced Architecture'],
        fullExplanation: 'Understanding $topic is essential because it bridges foundational theory with practical implementation.',
        coreValue: 'Critical mental model for modern systems.',
        prerequisiteConnection: 'Builds upon preceding core principles.',
        futureUnlocks: 'Unlocks deeper concurrent and architectural mastery.',
      );
    }
  }

  Future<List<Map<String, dynamic>>> getAvailableTracks() async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/curriculum/tracks');
      if (response is List) {
        return List<Map<String, dynamic>>.from(response);
      }
      return _defaultTracks;
    } catch (_) {
      return _defaultTracks;
    }
  }

  static const List<Map<String, dynamic>> _defaultTracks = [
    {
      'id': 'os',
      'title': 'Operating Systems',
      'description': 'Processes, threads, CPU scheduling, synchronization, deadlocks, and virtual memory.',
      'topics_count': 9,
      'difficulty': 'intermediate',
    },
    {
      'id': 'dbms',
      'title': 'Database Management Systems',
      'description': 'Relational model, normalization, B+ Trees, ACID transactions, and 2PL concurrency.',
      'topics_count': 6,
      'difficulty': 'intermediate',
    },
    {
      'id': 'ml',
      'title': 'Machine Learning',
      'description': 'Calculus & algebra, linear/logistic regression, decision trees, and neural networks.',
      'topics_count': 5,
      'difficulty': 'intermediate',
    },
    {
      'id': 'dsa',
      'title': 'Python & Data Structures',
      'description': 'Big-O complexity, linked lists, stacks, trees, and graph algorithms.',
      'topics_count': 5,
      'difficulty': 'beginner',
    },
  ];

  RoadmapModel _getOfflineFallbackRoadmap(String subject, String? goal) {
    final activeUser = OfflineStorageService().activeUserId;
    final isNewUser = activeUser != null && activeUser != 'demo-student-id-001';

    final isOs = subject.toLowerCase().contains('os') || subject.toLowerCase().contains('operat');
    if (isOs) {
      return RoadmapModel(
        id: 'os-offline-roadmap',
        title: 'Operating Systems Mastery Track',
        subject: 'Operating Systems',
        goal: goal ?? 'Master Operating Systems fundamentals and internal mechanics',
        totalSteps: 5,
        completedSteps: isNewUser ? 0 : 1,
        progressPercentage: isNewUser ? 0.0 : 20.0,
        status: isNewUser ? 'not_started' : 'in_progress',
        topics: [
          RoadmapTopicModel(
            orderIndex: 1,
            customTitle: 'OS Fundamentals & Architecture',
            description: 'Kernel vs user mode, system calls, and hardware abstraction.',
            difficulty: 'beginner',
            estimatedMinutes: 30,
            status: isNewUser ? 'not_started' : 'mastered',
            masteryScore: isNewUser ? 0.0 : 90.0,
            learningObjectives: const ['Understand user vs kernel mode', 'Explain traps and system calls'],
          ),
          RoadmapTopicModel(
            orderIndex: 2,
            customTitle: 'Processes & Lifecycle',
            description: 'Process structure, Process Control Block (PCB), states, and context switching.',
            difficulty: 'beginner',
            estimatedMinutes: 45,
            status: isNewUser ? 'locked' : 'in_progress',
            prerequisites: const ['OS Fundamentals & Architecture'],
            learningObjectives: const ['Diagram 5 process lifecycle states', 'Detail PCB data'],
          ),
          RoadmapTopicModel(
            orderIndex: 3,
            customTitle: 'CPU Scheduling Algorithms',
            description: 'FCFS, SJF, Round Robin, and Priority Scheduling.',
            difficulty: 'intermediate',
            estimatedMinutes: 50,
            status: 'locked',
            prerequisites: const ['Processes & Lifecycle'],
            learningObjectives: const ['Calculate average waiting time', 'Evaluate Round Robin time quantum'],
          ),
          RoadmapTopicModel(
            orderIndex: 4,
            customTitle: 'Process Synchronization & Concurrency',
            description: 'Race conditions, critical section, mutexes, and semaphores.',
            difficulty: 'intermediate',
            estimatedMinutes: 60,
            status: 'locked',
            prerequisites: const ['Processes & Lifecycle'],
            learningObjectives: const ['Mutual exclusion', 'Counting vs binary semaphores'],
          ),
          RoadmapTopicModel(
            orderIndex: 5,
            customTitle: 'Deadlocks & Banker\'s Algorithm',
            description: 'The four Coffman conditions, resource allocation graphs, and Banker\'s algorithm.',
            difficulty: 'advanced',
            estimatedMinutes: 60,
            status: 'locked',
            prerequisites: const ['Process Synchronization & Concurrency'],
            learningObjectives: const ['Four Coffman deadlock conditions', 'Banker\'s safety algorithm'],
          ),
        ],
      );
    }

    return RoadmapModel(
      id: 'general-offline-roadmap',
      title: '$subject Track',
      subject: subject,
      goal: goal ?? 'Learn $subject step-by-step',
      totalSteps: 3,
      completedSteps: 0,
      progressPercentage: 0.0,
      status: 'in_progress',
      topics: [
        RoadmapTopicModel(
          orderIndex: 1,
          customTitle: '$subject Fundamentals',
          description: 'Core concepts and basic definitions of $subject.',
          difficulty: 'beginner',
          estimatedMinutes: 30,
          status: 'in_progress',
        ),
        RoadmapTopicModel(
          orderIndex: 2,
          customTitle: '$subject Applied Principles',
          description: 'Practical usage and problem solving.',
          difficulty: 'intermediate',
          estimatedMinutes: 45,
          status: 'locked',
          prerequisites: ['$subject Fundamentals'],
        ),
        RoadmapTopicModel(
          orderIndex: 3,
          customTitle: '$subject Advanced Systems',
          description: 'Optimization and architectural depth.',
          difficulty: 'advanced',
          estimatedMinutes: 60,
          status: 'locked',
          prerequisites: ['$subject Applied Principles'],
        ),
      ],
    );
  }
}
