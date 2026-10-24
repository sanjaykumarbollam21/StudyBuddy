import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/teaching_model.dart';

class TeachingApiService {
  final ApiClient _client = ApiClient();

  Future<List<ActiveTeachingSessionModel>> getActiveSessions() async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/teaching/sessions/active');
      if (response is List) {
        return response
            .map((e) => ActiveTeachingSessionModel.fromJson(e as Map<String, dynamic>))
            .toList();
      }
      return [];
    } catch (_) {
      return [];
    }
  }

  Future<TeachingSessionDetailModel?> getSession(String sessionId) async {
    try {
      final response = await _client.get('${AppConfig.baseUrl}/teaching/sessions/$sessionId');
      return TeachingSessionDetailModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<TeachingTurnModel> startSession({
    required String topic,
    String? subject,
    String? documentId,
    String? documentName,
    String? documentText,
    List<Map<String, dynamic>>? documentChunks,
    String? studentGoal,
  }) async {
    final body = <String, dynamic>{
      'topic': topic,
      'subject': subject ?? 'General',
    };
    if (documentId != null) body['document_id'] = documentId;
    if (documentName != null) body['document_name'] = documentName;
    if (documentText != null) body['document_text'] = documentText;
    if (documentChunks != null) body['document_chunks'] = documentChunks;
    if (studentGoal != null) body['student_goal'] = studentGoal;

    try {
      final response = await _client.post(
        '${AppConfig.baseUrl}/teaching/start',
        body: body,
      );
      return TeachingTurnModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      // Offline / Demo fallback
      return TeachingTurnModel(
        sessionId: 'offline-teach-session-1',
        state: 'assess_prior_knowledge',
        teacherMessage: 'Before we start, what do you already know about $topic?',
        checkQuestion: 'Before we start, what do you already know about $topic?',
        masteryPercentage: 0.0,
        currentStepNumber: 1,
        totalSteps: 3,
        suggestedActions: [
          'I think it happens when a process gets stuck.',
          'I am completely new to this',
          'Just give me the basics',
        ],
      );
    }
  }

  Future<TeachingTurnModel> submitStudentTurn({
    required String sessionId,
    required String answer,
    String actionType = 'answer',
  }) async {
    final body = <String, dynamic>{
      'answer': answer,
      'action_type': actionType,
    };

    try {
      final response = await _client.post(
        '${AppConfig.baseUrl}/teaching/$sessionId/interact',
        body: body,
      );
      return TeachingTurnModel.fromJson(response as Map<String, dynamic>);
    } catch (_) {
      // Offline Socratic fallback
      final ansLower = answer.toLowerCase();
      if (ansLower.contains('cpu') || ansLower.contains('slow')) {
        return TeachingTurnModel(
          sessionId: sessionId,
          state: 'reteaching',
          teacherMessage:
              'You\'re thinking about performance, which is a reasonable connection, '
              'but that\'s not the cause of deadlock.\n\n'
              'Let\'s simplify it.\n\n'
              'Imagine two people: Person A has Key 1 and needs Key 2, while Person B has Key 2 and needs Key 1.\n\n'
              '🎯 If Person A has Key 1 and needs Key 2, while Person B has Key 2 and needs Key 1, what happens?',
          conceptTitle: 'Deadlock Definition',
          explanation: 'Deadlock occurs when processes are blocked waiting for resources held by each other.',
          analogy: 'Two people each holding one key waiting for the other key.',
          checkQuestion: 'If Person A has Key 1 and needs Key 2, while Person B has Key 2 and needs Key 1, what happens?',
          evaluation: TeachingEvaluationModel(
            verdict: 'misconception',
            feedback: 'You\'re thinking about performance, but deadlock is caused by circular resource locks.',
            isCorrect: false,
            misconception: 'CPU too slow',
          ),
          masteryPercentage: 0.0,
          currentStepNumber: 1,
          totalSteps: 3,
          suggestedActions: ['Neither can continue', 'Give me a hint'],
        );
      }

      if (ansLower.contains('waiting') || ansLower.contains('other') || ansLower.contains('neither') || ansLower.contains('has')) {
        return TeachingTurnModel(
          sessionId: sessionId,
          state: 'check_understanding',
          teacherMessage:
              'Exactly. You identified the key idea: circular waiting.\n\n'
              'Next, let\'s look at The Four Coffman Conditions:\n\n'
              'For a deadlock to arise, four conditions must hold simultaneously: Mutual Exclusion, Hold & Wait, No Preemption, and Circular Wait.\n\n'
              '🎯 Check your understanding:\n'
              'If the operating system can forcibly take back a resource, which condition is broken?',
          conceptTitle: 'The Four Coffman Conditions',
          explanation: 'All 4 conditions must hold simultaneously for a deadlock to exist.',
          analogy: 'Like a four-legged stool: break one leg and it cannot stand.',
          checkQuestion: 'If the operating system can forcibly take back a resource, which condition is broken?',
          evaluation: TeachingEvaluationModel(
            verdict: 'correct',
            feedback: 'Exactly. You identified the key idea: circular waiting.',
            isCorrect: true,
          ),
          masteryPercentage: 35.0,
          currentStepNumber: 2,
          totalSteps: 3,
          suggestedActions: ['No Preemption', 'Mutual Exclusion', 'Give me a hint'],
        );
      }

      return TeachingTurnModel(
        sessionId: sessionId,
        state: 'check_understanding',
        teacherMessage:
            'Good starting point. A deadlock is more specific: processes can become permanently '
            'blocked because each is waiting for a resource held by another.\n\n'
            'Think of two people each holding one key while waiting for the other\'s key.\n\n'
            '🎯 Check your understanding:\n'
            'Why can\'t either process continue?',
        conceptTitle: 'Deadlock Definition & Circular Waiting',
        explanation: 'Processes are permanently blocked waiting for resources held by another.',
        analogy: 'Two people holding keys waiting for the other.',
        checkQuestion: 'Why can\'t either process continue?',
        masteryPercentage: 15.0,
        currentStepNumber: 1,
        totalSteps: 3,
        suggestedActions: [
          'Because each one is waiting for something the other one has.',
          'Deadlock happens because the CPU is too slow.',
          'Give me a hint',
        ],
      );
    }
  }
}
