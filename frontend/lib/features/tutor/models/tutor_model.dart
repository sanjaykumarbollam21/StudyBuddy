class SourceCitationItem {
  final String documentId;
  final String documentName;
  final int? pageNumber;
  final String? sectionTitle;
  final String? chunkId;
  final double? similarityScore;

  SourceCitationItem({
    required this.documentId,
    required this.documentName,
    this.pageNumber,
    this.sectionTitle,
    this.chunkId,
    this.similarityScore,
  });

  factory SourceCitationItem.fromJson(Map<String, dynamic> json) {
    return SourceCitationItem(
      documentId: json['document_id'] as String? ?? '',
      documentName: json['document_name'] as String? ?? 'Study Notes',
      pageNumber: json['page_number'] as int?,
      sectionTitle: json['section_title'] as String?,
      chunkId: json['chunk_id'] as String?,
      similarityScore: (json['similarity_score'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'document_id': documentId,
      'document_name': documentName,
      'page_number': pageNumber,
      'section_title': sectionTitle,
      'chunk_id': chunkId,
      'similarity_score': similarityScore,
    };
  }
}

class TutorResponseModel {
  final String answer;
  final List<SourceCitationItem> sources;
  final String groundingMode;
  final bool contextUsed;
  final String? sessionId;

  TutorResponseModel({
    required this.answer,
    required this.sources,
    required this.groundingMode,
    required this.contextUsed,
    this.sessionId,
  });

  bool get hasSources => sources.isNotEmpty;

  factory TutorResponseModel.fromJson(Map<String, dynamic> json) {
    final rawSources = json['sources'] as List<dynamic>? ?? [];
    return TutorResponseModel(
      answer: json['answer'] as String? ?? '',
      sources: rawSources
          .map((s) => SourceCitationItem.fromJson(s as Map<String, dynamic>))
          .toList(),
      groundingMode: json['grounding_mode'] as String? ?? 'materials_plus_general',
      contextUsed: json['context_used'] as bool? ?? false,
      sessionId: json['session_id'] as String?,
    );
  }
}
