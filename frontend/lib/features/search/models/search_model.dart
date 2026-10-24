class SearchResultItem {
  final String chunkId;
  final String documentId;
  final String documentName;
  final String content;
  final int? pageNumber;
  final String? sectionTitle;
  final double similarity;
  final String scoreType;

  SearchResultItem({
    required this.chunkId,
    required this.documentId,
    required this.documentName,
    required this.content,
    this.pageNumber,
    this.sectionTitle,
    this.similarity = 0.0,
    this.scoreType = 'semantic',
  });

  String get similarityPercentage => '${(similarity * 100).round()}%';

  factory SearchResultItem.fromJson(Map<String, dynamic> json) {
    return SearchResultItem(
      chunkId: json['chunk_id'] as String? ?? '',
      documentId: json['document_id'] as String? ?? '',
      documentName: json['document_name'] as String? ?? 'Document',
      content: json['content'] as String? ?? '',
      pageNumber: json['page_number'] as int?,
      sectionTitle: json['section_title'] as String?,
      similarity: (json['similarity'] as num?)?.toDouble() ?? 0.0,
      scoreType: json['score_type'] as String? ?? 'semantic',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'chunk_id': chunkId,
      'document_id': documentId,
      'document_name': documentName,
      'content': content,
      'page_number': pageNumber,
      'section_title': sectionTitle,
      'similarity': similarity,
      'score_type': scoreType,
    };
  }
}

class SearchResponseModel {
  final String query;
  final int totalResults;
  final List<SearchResultItem> results;

  SearchResponseModel({
    required this.query,
    required this.totalResults,
    required this.results,
  });

  factory SearchResponseModel.fromJson(Map<String, dynamic> json) {
    final list = json['results'] as List<dynamic>? ?? [];
    return SearchResponseModel(
      query: json['query'] as String? ?? '',
      totalResults: json['total_results'] as int? ?? list.length,
      results: list
          .map((item) => SearchResultItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
