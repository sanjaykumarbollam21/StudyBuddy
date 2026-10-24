enum VoiceState {
  idle,
  listening,
  thinking,
  speaking,
  interrupted,
}

class MultimodalAnalysisModel {
  final String imageType;
  final String detectedTopic;
  final String title;
  final List<String> visualElements;
  final String extractedText;
  final String conceptualExplanation;
  final String spokenScript;
  final String checkQuestion;
  final List<String> suggestedVoicePrompts;
  final List<Map<String, dynamic>> ragCitations;

  MultimodalAnalysisModel({
    required this.imageType,
    required this.detectedTopic,
    required this.title,
    required this.visualElements,
    required this.extractedText,
    required this.conceptualExplanation,
    required this.spokenScript,
    required this.checkQuestion,
    this.suggestedVoicePrompts = const [],
    this.ragCitations = const [],
  });

  factory MultimodalAnalysisModel.fromJson(Map<String, dynamic> json) {
    return MultimodalAnalysisModel(
      imageType: json['image_type'] as String? ?? 'diagram',
      detectedTopic: json['detected_topic'] as String? ?? 'General',
      title: json['title'] as String? ?? 'Diagram Analysis',
      visualElements: (json['visual_elements'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      extractedText: json['extracted_text'] as String? ?? '',
      conceptualExplanation: json['conceptual_explanation'] as String? ?? '',
      spokenScript: json['spoken_script'] as String? ?? '',
      checkQuestion: json['check_question'] as String? ?? '',
      suggestedVoicePrompts: (json['suggested_voice_prompts'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      ragCitations: (json['rag_citations'] as List<dynamic>?)
              ?.map((e) => e as Map<String, dynamic>)
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'image_type': imageType,
      'detected_topic': detectedTopic,
      'title': title,
      'visual_elements': visualElements,
      'extracted_text': extractedText,
      'conceptual_explanation': conceptualExplanation,
      'spoken_script': spokenScript,
      'check_question': checkQuestion,
      'suggested_voice_prompts': suggestedVoicePrompts,
      'rag_citations': ragCitations,
    };
  }
}

class VoiceTurnModel {
  final String sessionId;
  final String intent;
  final String teacherReplyText;
  final String spokenText;
  final String pedagogicalState;
  final String? conceptTitle;
  final MultimodalAnalysisModel? multimodalAnalysis;
  final List<String> suggestedQuickActions;
  final List<Map<String, dynamic>> citations;

  VoiceTurnModel({
    required this.sessionId,
    required this.intent,
    required this.teacherReplyText,
    required this.spokenText,
    required this.pedagogicalState,
    this.conceptTitle,
    this.multimodalAnalysis,
    this.suggestedQuickActions = const [],
    this.citations = const [],
  });

  factory VoiceTurnModel.fromJson(Map<String, dynamic> json) {
    return VoiceTurnModel(
      sessionId: json['session_id'] as String? ?? '',
      intent: json['intent'] as String? ?? 'answer',
      teacherReplyText: json['teacher_reply_text'] as String? ?? '',
      spokenText: json['spoken_text'] as String? ?? '',
      pedagogicalState: json['pedagogical_state'] as String? ?? 'CHECK_UNDERSTANDING',
      conceptTitle: json['concept_title'] as String?,
      multimodalAnalysis: json['multimodal_analysis'] != null
          ? MultimodalAnalysisModel.fromJson(json['multimodal_analysis'] as Map<String, dynamic>)
          : null,
      suggestedQuickActions: (json['suggested_quick_actions'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      citations: (json['citations'] as List<dynamic>?)
              ?.map((e) => e as Map<String, dynamic>)
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'session_id': sessionId,
      'intent': intent,
      'teacher_reply_text': teacherReplyText,
      'spoken_text': spokenText,
      'pedagogical_state': pedagogicalState,
      'concept_title': conceptTitle,
      'multimodal_analysis': multimodalAnalysis?.toJson(),
      'suggested_quick_actions': suggestedQuickActions,
      'citations': citations,
    };
  }
}

class VoiceDialogueMessage {
  final String sender; // 'student' or 'teacher'
  final String text;
  final String? spokenText;
  final String? imageSnippet;
  final DateTime timestamp;

  VoiceDialogueMessage({
    required this.sender,
    required this.text,
    this.spokenText,
    this.imageSnippet,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}
