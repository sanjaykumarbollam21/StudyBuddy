class DocumentChunkItem {
  final String id;
  final int chunkIndex;
  final String content;
  final int? pageNumber;
  final String? sectionTitle;
  final int characterStart;
  final int characterEnd;
  final DateTime createdAt;

  DocumentChunkItem({
    required this.id,
    required this.chunkIndex,
    required this.content,
    this.pageNumber,
    this.sectionTitle,
    this.characterStart = 0,
    this.characterEnd = 0,
    required this.createdAt,
  });

  factory DocumentChunkItem.fromJson(Map<String, dynamic> json) {
    return DocumentChunkItem(
      id: json['id'] as String? ?? '',
      chunkIndex: json['chunk_index'] as int? ?? 0,
      content: json['content'] as String? ?? '',
      pageNumber: json['page_number'] as int?,
      sectionTitle: json['section_title'] as String?,
      characterStart: json['character_start'] as int? ?? 0,
      characterEnd: json['character_end'] as int? ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'chunk_index': chunkIndex,
      'content': content,
      'page_number': pageNumber,
      'section_title': sectionTitle,
      'character_start': characterStart,
      'character_end': characterEnd,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class DocumentItem {
  final String id;
  final String filename;
  final String? originalFilename;
  final String fileType;
  final int fileSizeBytes;
  final int pageCount;
  final int extractedCharacterCount;
  final int sectionCount;
  final int chunkCount;
  final String subjectName;
  final String collectionName;
  final String processingStatus;
  final String processingStage;
  final int processingProgress;
  final String embeddingStatus;
  final String? errorMessage;
  final String? previewText;
  final List<DocumentChunkItem> chunks;
  final DateTime createdAt;

  DocumentItem({
    required this.id,
    required this.filename,
    this.originalFilename,
    required this.fileType,
    required this.fileSizeBytes,
    required this.pageCount,
    this.extractedCharacterCount = 0,
    this.sectionCount = 0,
    this.chunkCount = 0,
    this.subjectName = 'General',
    this.collectionName = 'My Materials',
    this.processingStatus = 'ready',
    this.processingStage = 'ready',
    this.processingProgress = 100,
    this.embeddingStatus = 'ready',
    this.errorMessage,
    this.previewText,
    this.chunks = const [],
    required this.createdAt,
  });

  bool get isReady => processingStatus.toLowerCase() == 'ready';
  bool get isProcessing =>
      processingStatus.toLowerCase() == 'processing' ||
      processingStatus.toLowerCase() == 'uploading' ||
      processingStatus.toLowerCase() == 'uploaded' ||
      processingStatus.toLowerCase() == 'extracting' ||
      processingStatus.toLowerCase() == 'cleaning' ||
      processingStatus.toLowerCase() == 'chunking' ||
      processingStatus.toLowerCase() == 'indexing';
  bool get isFailed => processingStatus.toLowerCase() == 'failed';

  bool get isIndexed => embeddingStatus.toLowerCase() == 'ready';
  bool get isIndexing =>
      embeddingStatus.toLowerCase() == 'indexing' ||
      embeddingStatus.toLowerCase() == 'processing' ||
      embeddingStatus.toLowerCase() == 'pending';
  bool get isIndexFailed => embeddingStatus.toLowerCase() == 'failed';

  String get formattedSize {
    if (fileSizeBytes < 1024) return '$fileSizeBytes B';
    if (fileSizeBytes < 1024 * 1024) {
      return '${(fileSizeBytes / 1024).toStringAsFixed(1)} KB';
    }
    return '${(fileSizeBytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  factory DocumentItem.fromJson(Map<String, dynamic> json) {
    final rawStatus = json['status'] ?? json['processing_status'] ?? 'ready';
    final rawProgress = json['progress'] ?? json['processing_progress'] ?? 100;
    final rawStage = json['processing_stage'] ?? json['stage'] ?? rawStatus;
    final rawEmbStatus = json['embedding_status'] ?? 'ready';

    List<DocumentChunkItem> parsedChunks = [];
    if (json['chunks'] is List) {
      parsedChunks = (json['chunks'] as List)
          .map((c) => DocumentChunkItem.fromJson(c as Map<String, dynamic>))
          .toList();
    }

    return DocumentItem(
      id: json['id'] as String? ?? '',
      filename: json['filename'] as String? ?? 'Untitled',
      originalFilename: json['original_filename'] as String?,
      fileType: json['file_type'] as String? ?? 'pdf',
      fileSizeBytes: json['file_size_bytes'] as int? ?? 1024,
      pageCount: json['page_count'] as int? ?? 1,
      extractedCharacterCount: json['extracted_character_count'] as int? ?? 0,
      sectionCount: json['section_count'] as int? ?? 0,
      chunkCount: json['chunk_count'] as int? ?? parsedChunks.length,
      subjectName: json['subject_name'] as String? ?? 'General',
      collectionName: json['collection_name'] as String? ?? 'My Materials',
      processingStatus: rawStatus.toString(),
      processingStage: rawStage.toString(),
      processingProgress: (rawProgress is num) ? rawProgress.toInt() : 100,
      embeddingStatus: rawEmbStatus.toString(),
      errorMessage: json['error_message'] as String?,
      previewText: json['preview_text'] as String?,
      chunks: parsedChunks,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'] as String) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'filename': filename,
      'original_filename': originalFilename,
      'file_type': fileType,
      'file_size_bytes': fileSizeBytes,
      'page_count': pageCount,
      'extracted_character_count': extractedCharacterCount,
      'section_count': sectionCount,
      'chunk_count': chunkCount,
      'subject_name': subjectName,
      'collection_name': collectionName,
      'status': processingStatus,
      'processing_stage': processingStage,
      'progress': processingProgress,
      'embedding_status': embeddingStatus,
      'error_message': errorMessage,
      'preview_text': previewText,
      'chunks': chunks.map((c) => c.toJson()).toList(),
      'created_at': createdAt.toIso8601String(),
    };
  }
}
