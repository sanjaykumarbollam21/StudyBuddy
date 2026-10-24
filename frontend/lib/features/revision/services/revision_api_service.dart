import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/storage/offline_storage_service.dart';
import '../models/revision_model.dart';

class RevisionApiService {
  final ApiClient _client = ApiClient();

  Future<List<RevisionItemModel>> getDueReviews({int limit = 10}) async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/revision/due?limit=$limit');
      if (response is List) {
        return response
            .map((e) => RevisionItemModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return _getFallbackDueReviews();
    } catch (_) {
      final activeUser = OfflineStorageService().activeUserId;
      if (activeUser != null && activeUser != 'demo-student-id-001') {
        final offlineItems = await OfflineStorageService().loadRevisionItems();
        return offlineItems
            .map((e) => RevisionItemModel(
                  id: e['id'] as String? ?? 'item',
                  topicTitle: e['topic_title'] as String? ?? '',
                  conceptSummary: e['concept_summary'] as String? ?? '',
                  retrievalPrompt: e['retrieval_prompt'] as String? ?? '',
                  retrievalAnswer: e['retrieval_answer'] as String? ?? '',
                  intervalDays: e['interval_days'] as int? ?? 1,
                  repetitionCount: e['repetition_count'] as int? ?? 0,
                  easeFactor: (e['ease_factor'] as num?)?.toDouble() ?? 2.5,
                  masteryScore: (e['mastery_score'] as num?)?.toDouble() ?? 0.0,
                  daysOverdue: (e['days_overdue'] as num?)?.toDouble() ?? 0.0,
                  qualityHistory: const [],
                ))
            .toList();
      }
      return _getFallbackDueReviews();
    }
  }

  Future<SubmitReviewResponseModel> submitReview({
    required String itemId,
    required int qualityRating,
    String? studentRecall,
  }) async {
    final body = <String, dynamic>{
      'item_id': itemId,
      'quality_rating': qualityRating,
    };
    if (studentRecall != null) body['student_recall'] = studentRecall;

    try {
      final response = await _client.post(
        '${AppConfig.baseUrl}/revision/submit',
        body: body,
      );
      return SubmitReviewResponseModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      final isPassed = qualityRating >= 3;
      return SubmitReviewResponseModel(
        itemId: itemId,
        qualityRating: qualityRating,
        isPassed: isPassed,
        newIntervalDays: isPassed ? 6 : 1,
        newEaseFactor: 2.5,
        nextReviewDate: DateTime.now().add(Duration(days: isPassed ? 6 : 1)).toIso8601String(),
        updatedMasteryPercentage: isPassed ? 82.0 : 45.0,
        remediationAdvice: isPassed
            ? null
            : 'Retention lapsed on this concept. Launch Socratic AI Teacher to refresh intuition.',
      );
    }
  }

  Future<DailyAgendaModel> getDailyAgenda() async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/revision/agenda');
      return DailyAgendaModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      final activeUser = OfflineStorageService().activeUserId;
      if (activeUser != null && activeUser != 'demo-student-id-001') {
        final offlineItems = await OfflineStorageService().loadRevisionItems();
        return DailyAgendaModel(
          continueLearning: ContinueLearningInfoModel(
            topic: 'OS Fundamentals & Architecture',
            progressText: 'Step 1 of 5',
            subject: 'Operating Systems',
          ),
          dueForReviewCount: offlineItems.length,
          topWeakArea: WeakAreaInfoModel(
            concept: 'None',
            masteryPercentage: 100.0,
            topic: 'General',
          ),
          recommendedAction: 'Start your study session',
          examPriority: 'All Core Topics',
          reviewStreakDays: 0,
          retentionRatePercentage: 100.0,
        );
      }
      return DailyAgendaModel(
        continueLearning: ContinueLearningInfoModel(
          topic: 'Deadlocks & Banker\'s Algorithm',
          progressText: 'Step 3 of 5',
          subject: 'Operating Systems',
        ),
        dueForReviewCount: 3,
        topWeakArea: WeakAreaInfoModel(
          concept: 'Circular Wait',
          masteryPercentage: 42.0,
          topic: 'Deadlocks',
        ),
        recommendedAction: '5-minute active retrieval on 3 overdue concepts',
        examPriority: 'CPU Scheduling Algorithms',
        reviewStreakDays: 4,
        retentionRatePercentage: 86.5,
      );
    }
  }

  List<RevisionItemModel> _getFallbackDueReviews() {
    return [
      RevisionItemModel(
        id: 'fallback-rev-1',
        topicTitle: 'Deadlocks & Banker\'s Algorithm',
        conceptSummary: 'Deadlock conditions and prevention strategies.',
        retrievalPrompt: 'Without looking: Name all four Coffman deadlock conditions from memory, and explain how Circular Wait is prevented.',
        retrievalAnswer: '1. Mutual Exclusion\n2. Hold and Wait\n3. No Preemption\n4. Circular Wait\n\nTo eliminate Circular Wait: Enforce a global total ordering on resource requests (F: R -> N).',
        intervalDays: 1,
        repetitionCount: 1,
        easeFactor: 2.5,
        masteryScore: 45.0,
        daysOverdue: 2.0,
        qualityHistory: [2],
      ),
      RevisionItemModel(
        id: 'fallback-rev-2',
        topicTitle: 'Process Synchronization',
        conceptSummary: 'Critical section problem and semaphore primitives.',
        retrievalPrompt: 'Active Recall Challenge: State the three requirements for solving the Critical Section problem, and what occurs if Progress is violated.',
        retrievalAnswer: '1. Mutual Exclusion\n2. Progress\n3. Bounded Waiting\n\nIf Progress is violated, a deadlock or freeze occurs where processes in non-critical sections block others.',
        intervalDays: 3,
        repetitionCount: 2,
        easeFactor: 2.6,
        masteryScore: 68.0,
        daysOverdue: 1.0,
        qualityHistory: [4, 3],
      ),
      RevisionItemModel(
        id: 'fallback-rev-3',
        topicTitle: 'CPU Scheduling Algorithms',
        conceptSummary: 'Processor dispatching and queuing algorithms.',
        retrievalPrompt: 'Active Recall: What is the Convoy Effect in FCFS, and what happens when the Round Robin time quantum approaches infinity?',
        retrievalAnswer: 'Convoy Effect: Short processes stuck waiting behind a CPU-bound process.\n\nWhen quantum -> infinity, Round Robin degenerates into FCFS.',
        intervalDays: 6,
        repetitionCount: 3,
        easeFactor: 2.5,
        masteryScore: 78.0,
        daysOverdue: 0.5,
        qualityHistory: [4, 4, 4],
      ),
    ];
  }
}
