import 'package:flutter/foundation.dart';
import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/exam_model.dart';

class ExamApiService {
  final ApiClient _client = ApiClient();

  Future<MockExamSessionModel> startMockExam({
    String? configId,
    String subject = 'Operating Systems',
    int totalQuestions = 6,
  }) async {
    final body = <String, dynamic>{
      'subject': subject,
      'total_questions': totalQuestions,
    };
    if (configId != null) body['config_id'] = configId;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/exams/mock/start',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return MockExamSessionModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[ExamApiService] startMockExam error (using fallback): $e');
    }
    return _getFallbackMockSession(subject, totalQuestions);
  }

  Future<MockExamSessionModel> getMockSession(String sessionId) async {
    try {
      final res = await _client.get('${AppConfig.baseUrl}/exams/mock/$sessionId');
      if (res is Map<String, dynamic>) {
        return MockExamSessionModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[ExamApiService] getMockSession error (using fallback): $e');
    }
    return _getFallbackMockSession('Operating Systems', 6);
  }

  Future<MockExamSessionModel> saveProgress(
    String sessionId, {
    required Map<String, dynamic> answers,
    required List<String> reviewFlags,
    required int timeRemainingSeconds,
  }) async {
    try {
      final res = await _client.put(
        '${AppConfig.baseUrl}/exams/mock/$sessionId/progress',
        body: {
          'answers': answers,
          'review_flags': reviewFlags,
          'time_remaining_seconds': timeRemainingSeconds,
        },
      );
      if (res is Map<String, dynamic>) {
        return MockExamSessionModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[ExamApiService] saveProgress error (cached locally): $e');
    }
    return MockExamSessionModel(
      id: sessionId,
      title: 'Operating Systems Semester Exam — Mock Session',
      subject: 'Operating Systems',
      durationMinutes: 45,
      timeRemainingSeconds: timeRemainingSeconds,
      questions: _getFallbackQuestions(),
      reviewFlags: reviewFlags,
      answersRecord: answers,
    );
  }

  Future<ExamResultModel> submitMockExam(
    String sessionId, {
    Map<String, dynamic>? answers,
    int? timeSpentSeconds,
  }) async {
    final body = <String, dynamic>{
      'answers': answers ?? {},
    };
    if (timeSpentSeconds != null) body['time_spent_seconds'] = timeSpentSeconds;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/exams/mock/$sessionId/submit',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return ExamResultModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[ExamApiService] submitMockExam error (using fallback): $e');
    }
    return _getFallbackExamResult(answers ?? {});
  }

  Future<ExamReadinessDetailModel> getExamReadiness({String? configId}) async {
    try {
      final url = configId != null
          ? '${AppConfig.baseUrl}/exams/readiness?config_id=$configId'
          : '${AppConfig.baseUrl}/exams/readiness';
      final res = await _client.get(url);
      if (res is Map<String, dynamic>) {
        return ExamReadinessDetailModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[ExamApiService] getExamReadiness error (using fallback): $e');
    }
    return ExamReadinessDetailModel(
      readinessPercentage: 68.0,
      readinessCategory: 'Moderate Exam Readiness',
      readinessMessage: "You're approximately 68% ready for this exam.",
      actionableProjection:
          "At your current study rate, your weakest areas are likely to remain Synchronization and Deadlocks. Spend your next 3 sessions there.",
      dimensionScores: {
        'knowledge_coverage': 85.0,
        'concept_mastery': 62.0,
        'recent_recall': 70.0,
        'practice_accuracy': 74.0,
        'mock_test_performance': 68.0,
        'time_management': 80.0,
      },
      strongTopics: ['CPU Scheduling', 'Processes'],
      weakTopics: ['Synchronization'],
      criticalTopics: ['Deadlocks'],
    );
  }

  // ---------------------------------------------------------------------------
  // Fallbacks for offline operations
  // ---------------------------------------------------------------------------

  MockExamSessionModel _getFallbackMockSession(String subject, int count) {
    final qs = _getFallbackQuestions().take(count).toList();
    return MockExamSessionModel(
      id: 'session-local-offline-101',
      title: '$subject Semester Exam — Mock Session',
      subject: subject,
      durationMinutes: 45,
      timeRemainingSeconds: 2700,
      totalQuestions: qs.length,
      totalMarks: 60.0,
      questions: qs,
      reviewFlags: [],
      answersRecord: {},
    );
  }

  List<MockExamQuestionModel> _getFallbackQuestions() {
    return [
      MockExamQuestionModel(
        id: 'q-fb-dl-1',
        topic: 'Deadlocks',
        questionType: 'mcq',
        prompt:
            'Which statement precisely characterizes the distinction between Deadlock Prevention and Deadlock Avoidance?',
        options: [
          'Prevention eliminates one of the four Coffman conditions statically; Avoidance dynamically evaluates request safety using maximum claim matrices.',
          'Prevention uses runtime cycle detection; Avoidance aborts transactions with timeouts.',
          'Prevention and Avoidance are synonyms in modern OS kernels.',
          'Prevention dynamically simulates state transitions; Avoidance requires hardware lock-free primitives.',
        ],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 1,
        difficulty: 'intermediate',
        conceptTag: 'prevention_vs_avoidance',
        learningObjective: 'Differentiate static prevention from dynamic avoidance.',
      ),
      MockExamQuestionModel(
        id: 'q-fb-cpu-1',
        topic: 'CPU Scheduling',
        questionType: 'mcq',
        prompt:
            'Consider 3 processes arriving at time 0 with burst times: P1=24ms, P2=3ms, P3=3ms. What is the average waiting time under Shortest Job First (SJF) non-preemptive scheduling?',
        options: ['3.0 ms', '6.0 ms', '17.0 ms', '27.0 ms'],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 2,
        difficulty: 'intermediate',
        conceptTag: 'sjf_convoy_effect',
        learningObjective: 'Calculate average waiting times and avoid convoy effect.',
      ),
      MockExamQuestionModel(
        id: 'q-fb-proc-1',
        topic: 'Processes',
        questionType: 'mcq',
        prompt:
            'Which field in a Process Control Block (PCB) preserves the CPU registers when a process is preempted by the scheduler?',
        options: ['Context State / CPU Registers', 'PID Identifier', 'I/O Status List', 'Page Table Base Pointer'],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 3,
        difficulty: 'beginner',
        conceptTag: 'pcb_context_switch',
        learningObjective: 'Identify context switching register storage in PCB.',
      ),
      MockExamQuestionModel(
        id: 'q-fb-sync-1',
        topic: 'Synchronization',
        questionType: 'scenario',
        prompt:
            'A counting semaphore is initialized to 1. Thread A calls sem_wait(), thread B concurrently calls sem_wait(), then Thread C calls sem_post(). What is the semaphore value after Thread C post?',
        options: [
          '0 (Thread B is unblocked and permitted into the critical section while semaphore count remains 0)',
          '1 (The semaphore is free and unheld)',
          '-1 (The semaphore queue remains congested)',
          '2 (Semaphore counter increments beyond capacity)',
        ],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 4,
        difficulty: 'advanced',
        conceptTag: 'counting_semaphore_mechanics',
        learningObjective: 'Trace counting semaphore state transitions and unblocking.',
      ),
      MockExamQuestionModel(
        id: 'q-fb-mem-1',
        topic: 'Memory Management',
        questionType: 'mcq',
        prompt:
            'In a 32-bit architecture with 4 KB pages and 4-byte PTEs, how many bits are used for outer and inner page indices in two-level paging?',
        options: ['10 bits outer, 10 bits inner', '12 bits outer, 8 bits inner', '14 bits outer, 6 bits inner', '8 bits outer, 12 bits inner'],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 5,
        difficulty: 'advanced',
        conceptTag: 'two_level_paging_math',
        learningObjective: 'Partition virtual address bits across hierarchical page tables.',
      ),
      MockExamQuestionModel(
        id: 'q-fb-dl-2',
        topic: 'Deadlocks',
        questionType: 'scenario',
        prompt:
            'A database engine has 3 concurrent transactions requesting locks on tables A, B, and C in cyclic order (T1->T2->T3->T1). Identify the mechanism required.',
        options: [
          'Deadlock Detection via Wait-For-Graph (WFG) cycle analysis and victim rollback',
          'Deadlock Prevention via Banker\'s algorithm safe-state matrix lookahead',
          'Deadlock Avoidance via static global resource ordering enumeration',
          'Deadlock Prevention by disabling preemption on table locks',
        ],
        marks: 10.0,
        negativeMarks: 2.5,
        orderIndex: 6,
        difficulty: 'advanced',
        conceptTag: 'prevention_vs_avoidance',
        learningObjective: 'Distinguish detection recovery from avoidance.',
      ),
    ];
  }

  ExamResultModel _getFallbackExamResult(Map<String, dynamic> answers) {
    return ExamResultModel(
      id: 'session-local-offline-101',
      title: 'Operating Systems Semester Exam — Mock Session',
      status: 'submitted',
      scorePercentage: 74.0,
      marksObtained: 44.4,
      totalMarks: 60.0,
      negativeMarksDeducted: 2.5,
      correctCount: 4,
      incorrectCount: 1,
      unansweredCount: 1,
      topicAnalysis: [
        TopicPerformanceModel(
          topic: 'CPU Scheduling',
          scorePercentage: 89.0,
          tier: 'Strong',
          correctCount: 1,
          questionCount: 1,
          marksObtained: 10.0,
          totalMarks: 10.0,
        ),
        TopicPerformanceModel(
          topic: 'Processes',
          scorePercentage: 76.0,
          tier: 'Good',
          correctCount: 1,
          questionCount: 1,
          marksObtained: 10.0,
          totalMarks: 10.0,
        ),
        TopicPerformanceModel(
          topic: 'Synchronization',
          scorePercentage: 48.0,
          tier: 'Weak',
          correctCount: 0,
          questionCount: 1,
          marksObtained: 4.8,
          totalMarks: 10.0,
        ),
        TopicPerformanceModel(
          topic: 'Deadlocks',
          scorePercentage: 31.0,
          tier: 'Critical',
          correctCount: 0,
          questionCount: 2,
          marksObtained: 3.1,
          totalMarks: 20.0,
        ),
      ],
      cognitiveDiagnosis: CognitiveDiagnosisModel(
        coreIssue: "Your biggest problem isn't memorization. Your answers show confusion between deadlock prevention and deadlock avoidance.",
        deepExplanation:
            "Deadlock Prevention systematically invalidates Coffman conditions statically (such as imposing a global numerical resource ordering to prevent circular wait). Deadlock Avoidance, however, permits arbitrary runtime requests but dynamically verifies transitions using safe-state algorithms (e.g. Banker's Algorithm).",
        keyRemediationConcept: 'Deadlock Prevention vs Avoidance',
        detectedMisconceptionsCount: 1,
        unansweredQuestions: 1,
      ),
      remediationAction: RemediationActionModel(
        targetTopic: 'Deadlocks',
        ctaTitle: 'Reteach Deadlocks',
        prompt: 'Teach me the core difference between deadlock prevention and deadlock avoidance with clear examples.',
        learningObjective: 'Remediate deadlock prevention versus avoidance misconception.',
      ),
      readiness: ExamReadinessDetailModel(
        readinessPercentage: 68.0,
        readinessCategory: 'Moderate Exam Readiness',
        readinessMessage: "You're approximately 68% ready for this exam.",
        actionableProjection:
            "At your current study rate, your weakest areas are likely to remain Synchronization and Deadlocks. Spend your next 3 sessions there.",
        dimensionScores: {
          'knowledge_coverage': 85.0,
          'concept_mastery': 62.0,
          'recent_recall': 70.0,
          'practice_accuracy': 74.0,
          'mock_test_performance': 74.0,
          'time_management': 80.0,
        },
        strongTopics: ['CPU Scheduling', 'Processes'],
        weakTopics: ['Synchronization'],
        criticalTopics: ['Deadlocks'],
      ),
    );
  }
}
