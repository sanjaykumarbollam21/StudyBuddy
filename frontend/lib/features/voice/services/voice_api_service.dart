import 'package:flutter/foundation.dart';
import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/voice_model.dart';

class VoiceApiService {
  final ApiClient _client = ApiClient();

  Future<VoiceTurnModel> sendVoiceTurn({
    required String transcript,
    String? sessionId,
    String currentTopic = 'Deadlocks',
    String currentSubject = 'Operating Systems',
    String? imageData,
    String? imageFilename,
    String? documentId,
    int? pageNumber,
  }) async {
    final body = <String, dynamic>{
      'transcript': transcript,
      'current_topic': currentTopic,
      'current_subject': currentSubject,
    };
    if (sessionId != null) body['session_id'] = sessionId;
    if (imageData != null) body['image_data'] = imageData;
    if (imageFilename != null) body['image_filename'] = imageFilename;
    if (documentId != null) body['document_id'] = documentId;
    if (pageNumber != null) body['page_number'] = pageNumber;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/voice/chat',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return VoiceTurnModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[VoiceApiService] sendVoiceTurn error (using fallback): $e');
    }

    return _getFallbackVoiceTurn(
      transcript: transcript,
      currentTopic: currentTopic,
      hasImage: imageData != null || imageFilename != null,
      pageNumber: pageNumber,
    );
  }

  Future<MultimodalAnalysisModel> analyzeImage({
    String? imageData,
    String? imageFilename,
    String? userPrompt,
    String currentTopic = 'Deadlocks',
    String? documentId,
    int? pageNumber,
  }) async {
    final body = <String, dynamic>{
      'current_topic': currentTopic,
    };
    if (imageData != null) body['image_data'] = imageData;
    if (imageFilename != null) body['image_filename'] = imageFilename;
    if (userPrompt != null) body['user_prompt'] = userPrompt;
    if (documentId != null) body['document_id'] = documentId;
    if (pageNumber != null) body['page_number'] = pageNumber;

    try {
      final res = await _client.post(
        '${AppConfig.baseUrl}/multimodal/analyze',
        body: body,
      );
      if (res is Map<String, dynamic>) {
        return MultimodalAnalysisModel.fromJson(res);
      }
    } catch (e) {
      debugPrint('[VoiceApiService] analyzeImage error (using fallback): $e');
    }

    return _getFallbackMultimodalAnalysis(currentTopic, pageNumber);
  }

  VoiceTurnModel _getFallbackVoiceTurn({
    required String transcript,
    required String currentTopic,
    bool hasImage = false,
    int? pageNumber,
  }) {
    final lower = transcript.toLowerCase();

    if (hasImage || lower.contains('diagram') || lower.contains('image')) {
      final mm = _getFallbackMultimodalAnalysis(currentTopic, pageNumber);
      return VoiceTurnModel(
        sessionId: 'session-voice-offline-1',
        intent: 'image_explanation',
        teacherReplyText:
            '### 🖼️ ${mm.title}\n\n${mm.conceptualExplanation}\n\n**Visual Elements Detected:**\n- Process P1 holding R1, waiting for R2\n- Process P2 holding R2, waiting for R1\n- Circular Wait dependency loop\n\n🎯 **Check your understanding:**\n${mm.checkQuestion}',
        spokenText: mm.spokenScript,
        pedagogicalState: 'CHECK_UNDERSTANDING',
        conceptTitle: mm.detectedTopic,
        multimodalAnalysis: mm,
        suggestedQuickActions: mm.suggestedVoicePrompts,
      );
    }

    if (lower.contains('page') || pageNumber != null) {
      final page = pageNumber ?? 42;
      return VoiceTurnModel(
        sessionId: 'session-voice-offline-1',
        intent: 'page_explanation',
        teacherReplyText:
            '### 📄 Document Analysis — Page $page\n\nPage $page discusses Coffman conditions and static deadlock prevention by strictly ordering resource enumerations.\n\n🎯 **Check your understanding:**\nHow does imposing a global numbering on all resources eliminate circular wait?',
        spokenText:
            'Turning to page $page. This section explains how strict resource ordering breaks circular wait. If every process requests resources in increasing numerical order, can a cycle ever form?',
        pedagogicalState: 'CHECK_UNDERSTANDING',
        conceptTitle: '$currentTopic — Page $page',
        suggestedQuickActions: ['Explain simpler', 'Quiz me on this page', 'Next concept'],
      );
    }

    if (lower.contains('hint')) {
      return VoiceTurnModel(
        sessionId: 'session-voice-offline-1',
        intent: 'hint',
        teacherReplyText:
            '💡 **Socratic Hint:** Think about what happens if you assign a permanent integer order F(R) to every resource and require threads to request them only in strictly increasing order.',
        spokenText:
            'Here is a hint: what if we assign every resource a number, and you can only request them in increasing order? Can you ever get a circle?',
        pedagogicalState: 'REMEDIATE',
        conceptTitle: currentTopic,
        suggestedQuickActions: ['I understand now', 'Give another hint', 'Explain simpler'],
      );
    }

    if (lower.contains('simpler') || lower.contains('easier') || lower.contains('dont understand')) {
      return VoiceTurnModel(
        sessionId: 'session-voice-offline-1',
        intent: 'simplify',
        teacherReplyText:
            '💡 **Real-Life Analogy:** Imagine a circular dining table where 5 philosophers each need 2 forks to eat, but only pick up their left fork. Everyone is stuck waiting forever for the fork on their right!',
        spokenText:
            'Let us use a simple picture. Imagine five people around a table who each need two forks to eat. If everyone grabs the left fork at the same time, nobody can eat and everyone waits forever. That is deadlock!',
        pedagogicalState: 'REMEDIATE',
        conceptTitle: currentTopic,
        suggestedQuickActions: ['How do we fix it?', 'Quiz me', 'Explain Banker algorithm'],
      );
    }

    if (lower.contains('quiz')) {
      return VoiceTurnModel(
        sessionId: 'session-voice-offline-1',
        intent: 'quiz_me',
        teacherReplyText:
            '🎯 **Knowledge Check:**\nWhich of the four Coffman conditions allows the operating system to forcibly reclaim a resource from a blocked process?',
        spokenText:
            'Here is a quick question to test your knowledge: which Coffman condition lets the operating system take back a resource from a waiting process?',
        pedagogicalState: 'CHECK_UNDERSTANDING',
        conceptTitle: currentTopic,
        suggestedQuickActions: ['Preemption', 'Mutual Exclusion', 'Give me a hint'],
      );
    }

    // Default conversational explanation
    return VoiceTurnModel(
      sessionId: 'session-voice-offline-1',
      intent: 'explain_topic',
      teacherReplyText:
          '### 📚 $currentTopic Overview\n\nA deadlock occurs when a set of concurrent processes are permanently blocked because each process holds resources while waiting for others.\n\n🎯 **Check your understanding:**\nName any two of the four Coffman conditions required for a deadlock.',
      spokenText:
          'A deadlock happens when processes get permanently stuck waiting on each other. Tell me: what two conditions must be true for this freeze to happen?',
      pedagogicalState: 'CHECK_UNDERSTANDING',
      conceptTitle: currentTopic,
      suggestedQuickActions: ['Mutual exclusion and hold and wait', 'Give me a hint', 'Make it easier'],
    );
  }

  MultimodalAnalysisModel _getFallbackMultimodalAnalysis(String topic, int? pageNumber) {
    final pageInfo = pageNumber != null ? ' (Page $pageNumber)' : '';
    return MultimodalAnalysisModel(
      imageType: 'diagram',
      detectedTopic: 'Deadlocks & Resource Allocation',
      title: 'Resource Allocation Graph & Wait-For-Graph Cycle$pageInfo',
      visualElements: [
        'Process P1 holds Resource R1 and requests Resource R2',
        'Process P2 holds Resource R2 and requests Resource R1',
        'Closed directed cycle detected: P1 -> R2 -> P2 -> R1 -> P1',
      ],
      extractedText: 'P1 -> R2; P2 -> R1; Claim: Circular Wait deadlock.',
      conceptualExplanation:
          'This diagram illustrates a classic Wait-For-Graph. Because directed edges form a closed cycle in a single-instance system, a deadlock is present. Breaking circular wait via global resource ordering prevents this graph cycle.',
      spokenScript:
          'Looking at this diagram, I see a clear cycle between Process 1 and Process 2. They are each holding what the other needs! Which Coffman condition does this closed chain represent?',
      checkQuestion: 'Which Coffman condition is satisfied by this closed directed loop of processes and resources?',
      suggestedVoicePrompts: [
        'How do we break this circular wait?',
        'Would Banker algorithm prevent this?',
        'What is deadlock avoidance?',
      ],
      ragCitations: [
        {
          'document_id': 'doc-os-silberschatz',
          'page_number': pageNumber ?? 42,
          'snippet': 'A cycle in a single-unit resource allocation graph implies deadlock.',
        }
      ],
    );
  }
}
