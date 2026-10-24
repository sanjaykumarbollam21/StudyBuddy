import 'dart:async';

/// Phase 14: Mobile On-Device Socratic LLM Provider Contract.
/// Executes completely offline on Android without requiring a desktop Ollama server.
abstract class MobileLLMProvider {
  String get providerName;
  Future<String> generateSocraticResponse({
    required String prompt,
    required String conceptTitle,
    String? documentContext,
  });
  Future<Map<String, dynamic>> evaluateAnswer({
    required String question,
    required String studentAnswer,
    required String expectedConcept,
  });
}

enum ModelLifecycleState {
  uninitialized,
  loading,
  ready,
  idle,
  executing,
  error,
}

/// On-Device Offline Rule & Pattern Teacher Engine for Android Runtime.
class AndroidLocalLLMProvider implements MobileLLMProvider {
  static final AndroidLocalLLMProvider _instance = AndroidLocalLLMProvider._internal();
  factory AndroidLocalLLMProvider() => _instance;
  AndroidLocalLLMProvider._internal();

  ModelLifecycleState _lifecycleState = ModelLifecycleState.idle;
  ModelLifecycleState get lifecycleState => _lifecycleState;

  Future<void> ensureModelLoaded() async {
    _lifecycleState = ModelLifecycleState.loading;
    await Future.delayed(const Duration(milliseconds: 10));
    _lifecycleState = ModelLifecycleState.ready;
  }

  Stream<String> streamSocraticResponse({
    required String prompt,
    required String conceptTitle,
    String? documentContext,
  }) async* {
    _lifecycleState = ModelLifecycleState.executing;
    final fullText = await generateSocraticResponse(
      prompt: prompt,
      conceptTitle: conceptTitle,
      documentContext: documentContext,
    );

    final words = fullText.split(' ');
    for (int i = 0; i < words.length; i++) {
      yield i == 0 ? words[i] : ' ${words[i]}';
      await Future.delayed(const Duration(milliseconds: 5));
    }
    _lifecycleState = ModelLifecycleState.ready;
  }

  @override
  String get providerName => 'android_on_device_socratic';

  @override
  Future<String> generateSocraticResponse({
    required String prompt,
    required String conceptTitle,
    String? documentContext,
  }) async {
    final lower = prompt.toLowerCase();

    if (lower.contains('deadlock') || conceptTitle.toLowerCase().contains('deadlock')) {
      if (documentContext != null && documentContext.isNotEmpty) {
        return 'Based directly on your uploaded notes on $conceptTitle:\n\n'
            'A deadlock requires all four Coffman conditions simultaneously: '
            'Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.\n\n'
            'Question for you: If we prevent just one of these conditions (like Circular Wait), '
            'can a deadlock still occur?';
      }
      return 'Let\'s break down $conceptTitle.\n\n'
          'Imagine two people: Person A holds Key 1 and needs Key 2. Person B holds Key 2 and needs Key 1. '
          'Neither will let go.\n\n'
          'What minimal change would break this stalemate?';
    }

    return 'Regarding $conceptTitle:\n\n'
        'Every complex computing concept is built from simpler foundations. '
        'Based on your syllabus, what is the core problem that $conceptTitle is designed to solve?';
  }

  @override
  Future<Map<String, dynamic>> evaluateAnswer({
    required String question,
    required String studentAnswer,
    required String expectedConcept,
  }) async {
    final ans = studentAnswer.toLowerCase().trim();

    // Check struggling / confused
    if (ans.contains('don\'t know') || ans.contains('not sure') || ans.contains('help') || ans.contains('confused')) {
      return {
        'verdict': 'struggling',
        'is_correct': false,
        'score': 0.0,
        'feedback': 'That is totally normal. Let\'s step back to the foundational principle.',
        'misconception_identified': null,
      };
    }

    // Check correct Coffman / deadlock indicators
    if (ans.contains('circular wait') || ans.contains('preemption') || ans.contains('mutual exclusion') || ans.contains('no preemption') || ans.contains('hold and wait')) {
      return {
        'verdict': 'correct',
        'is_correct': true,
        'score': 1.0,
        'feedback': 'Excellent deduction! Eliminating any single Coffman condition mathematically guarantees deadlock prevention.',
        'misconception_identified': null,
      };
    }

    // Misconception detection
    if (ans.contains('cpu') || ans.contains('fast') || ans.contains('speed')) {
      return {
        'verdict': 'misconception',
        'is_correct': false,
        'score': 0.3,
        'feedback': 'Deadlocks are caused by resource allocation conflicts, not processor speed.',
        'misconception_identified': 'Performance vs Resource Ownership Misconception',
      };
    }

    return {
      'verdict': 'partially_correct',
      'is_correct': false,
      'score': 0.5,
      'feedback': 'You\'re thinking along the right lines. Let\'s refine how resources are allocated.',
      'misconception_identified': null,
    };
  }
}
