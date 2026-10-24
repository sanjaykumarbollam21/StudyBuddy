import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../../../core/storage/offline_storage_service.dart';
import '../models/practice_model.dart';

class PracticeApiService {
  final ApiClient _client = ApiClient();

  Future<QuizSessionModel> startSession({
    required String topic,
    String sessionMode = 'practice',
    int count = 5,
    String? difficulty,
    String? documentId,
  }) async {
    final body = <String, dynamic>{
      'topic': topic,
      'session_mode': sessionMode,
      'count': count,
    };
    if (difficulty != null) body['difficulty'] = difficulty;
    if (documentId != null) body['document_id'] = documentId;

    try {
      final response = await _client.post(
        '${AppConfig.baseUrl}/practice/sessions/start',
        body: body,
      );
      return QuizSessionModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      return _getOfflineFallbackSession(topic, sessionMode);
    }
  }

  Future<SubmitAnswerResponseModel> submitAnswer({
    required String sessionId,
    required String questionId,
    required String studentResponse,
  }) async {
    final body = <String, dynamic>{
      'question_id': questionId,
      'student_response': studentResponse,
    };

    try {
      final response = await _client.post(
        '${AppConfig.baseUrl}/practice/sessions/$sessionId/answer',
        body: body,
      );
      return SubmitAnswerResponseModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      final isCorrect = studentResponse.toLowerCase().contains('preemption') ||
          studentResponse.toLowerCase().contains('true') ||
          studentResponse.toLowerCase().contains('progress') ||
          studentResponse.toLowerCase().contains('convoy');

      return SubmitAnswerResponseModel(
        evaluation: EvaluationDetailsModel(
          verdict: isCorrect ? 'correct' : 'incorrect',
          isCorrect: isCorrect,
          score: isCorrect ? 1.0 : 0.0,
          feedback: isCorrect
              ? 'Correct! You demonstrated clear conceptual mastery.'
              : 'Incorrect. Coffman deadlock conditions require Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.',
          explanation: 'When preemption is allowed, the operating system can take back resources, preventing deadlock.',
          misconceptionIdentified: isCorrect
              ? null
              : 'Misconception: Mistaking Mutual Exclusion as a preventative measure instead of a deadlock prerequisite.',
          remediationAdvice: isCorrect
              ? null
              : 'Revisit Coffman Conditions with Socratic AI Teacher to master resource allocation invariants.',
          conceptTag: 'deadlocks',
        ),
        sessionScorePercentage: isCorrect ? 100.0 : 0.0,
        updatedMasteryPercentage: isCorrect ? 85.0 : 45.0,
        isSessionCompleted: true,
        currentQuestionIndex: 1,
        totalQuestions: 1,
        nextQuestion: null,
      );
    }
  }

  Future<List<PracticeHistoryItemModel>> getPracticeHistory({int limit = 20}) async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/practice/history?limit=$limit');
      if (response is List) {
        return response
            .map((e) => PracticeHistoryItemModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return _getOfflineFallbackHistory();
    } catch (_) {
      final activeUser = OfflineStorageService().activeUserId;
      if (activeUser != null && activeUser != 'demo-student-id-001') {
        return [];
      }
      return _getOfflineFallbackHistory();
    }
  }

  Future<List<WeakAreaItemModel>> getWeakAreas() async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/practice/weak-areas');
      if (response is List) {
        return response
            .map((e) => WeakAreaItemModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return _getOfflineFallbackWeakAreas();
    } catch (_) {
      final activeUser = OfflineStorageService().activeUserId;
      if (activeUser != null && activeUser != 'demo-student-id-001') {
        return [];
      }
      return _getOfflineFallbackWeakAreas();
    }
  }

  QuizSessionModel _getOfflineFallbackSession(String topic, String sessionMode) {
    return QuizSessionModel(
      sessionId: 'offline-quiz-session-1',
      title: '$topic Practice Quiz',
      topic: topic,
      sessionMode: sessionMode,
      totalQuestions: 2,
      currentQuestionIndex: 0,
      status: 'in_progress',
      currentQuestion: QuestionModel(
        id: 'q-offline-1',
        orderIndex: 1,
        questionType: 'mcq',
        prompt: 'Which of the following is NOT one of the four necessary Coffman conditions for a deadlock to occur?',
        options: [
          'Mutual Exclusion',
          'Hold and Wait',
          'Preemption Allowed',
          'Circular Wait',
        ],
        difficulty: 'beginner',
        learningObjective: 'Identify Coffman conditions for deadlock.',
        conceptTag: 'coffman_conditions',
      ),
    );
  }

  List<PracticeHistoryItemModel> _getOfflineFallbackHistory() {
    return [
      PracticeHistoryItemModel(
        id: 'hist-1',
        title: 'Operating Systems Practice Quiz',
        topic: 'Deadlocks & Banker\'s Algorithm',
        sessionMode: 'practice',
        totalQuestions: 5,
        scorePercentage: 80.0,
        status: 'completed',
        createdAt: 'Yesterday',
      ),
      PracticeHistoryItemModel(
        id: 'hist-2',
        title: 'DBMS ACID & Concurrency Quiz',
        topic: 'Two-Phase Locking (2PL)',
        sessionMode: 'practice',
        totalQuestions: 5,
        scorePercentage: 60.0,
        status: 'completed',
        createdAt: '2 days ago',
      ),
    ];
  }

  List<WeakAreaItemModel> _getOfflineFallbackWeakAreas() {
    return [
      WeakAreaItemModel(
        topic: 'Deadlocks',
        masteryPercentage: 45.0,
        timesPracticed: 3,
        primaryMisconception: 'Confusion regarding Circular Wait vs Resource Ordering elimination.',
        totalMisconceptionsLogged: 2,
        remediationAction: 'Re-teach \'Deadlocks\' with Socratic AI Teacher',
      ),
      WeakAreaItemModel(
        topic: 'Process Synchronization',
        masteryPercentage: 62.0,
        timesPracticed: 4,
        primaryMisconception: 'Counting Semaphore vs Binary Semaphore boundary condition.',
        totalMisconceptionsLogged: 1,
        remediationAction: 'Re-teach \'Process Synchronization\' with Socratic AI Teacher',
      ),
    ];
  }
}
