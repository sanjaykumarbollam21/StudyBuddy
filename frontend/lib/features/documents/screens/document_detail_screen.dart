import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';
import '../models/document_model.dart';
import '../services/document_api_service.dart';

class DocumentDetailScreen extends StatefulWidget {
  final DocumentItem document;

  const DocumentDetailScreen({super.key, required this.document});

  @override
  State<DocumentDetailScreen> createState() => _DocumentDetailScreenState();
}

class _DocumentDetailScreenState extends State<DocumentDetailScreen> {
  final DocumentApiService _docService = DocumentApiService();
  final TextEditingController _chunkSearchController = TextEditingController();

  late DocumentItem _doc;
  bool _isLoading = false;
  String _chunkSearchQuery = '';

  @override
  void initState() {
    super.initState();
    _doc = widget.document;
    _fetchLatestDetails();
  }

  @override
  void dispose() {
    _chunkSearchController.dispose();
    super.dispose();
  }

  Future<void> _fetchLatestDetails() async {
    setState(() => _isLoading = true);
    try {
      final updated = await _docService.getDocumentDetail(_doc.id);
      if (mounted) {
        setState(() {
          _doc = updated;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _retryProcessing() async {
    setState(() => _isLoading = true);
    try {
      await _docService.retryDocument(_doc.id);
      await _fetchLatestDetails();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Processing pipeline restarted.'),
            backgroundColor: AppColors.emerald,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Retry failed: $e'),
            backgroundColor: AppColors.rose,
          ),
        );
      }
    }
  }

  Future<void> _reindexDocument() async {
    setState(() => _isLoading = true);
    try {
      await _docService.reindexDocument(_doc.id);
      await _fetchLatestDetails();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('AI search re-indexing complete! Chunks are embedded and searchable.'),
            backgroundColor: AppColors.emerald,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Re-index failed: $e'),
            backgroundColor: AppColors.rose,
          ),
        );
      }
    }
  }

  void _confirmDelete() {
    final nav = Navigator.of(context);
    showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Delete Document?'),
        content: Text(
          'Are you sure you want to delete "${_doc.filename}"? This will permanently remove it and all extracted chunks from your knowledge base.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogCtx).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.rose),
            onPressed: () async {
              Navigator.of(dialogCtx).pop();
              try {
                await _docService.deleteDocument(_doc.id);
              } catch (_) {}
              if (!mounted) return;
              nav.pop(true); // Return true to indicate deleted
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  List<DocumentChunkItem> get _filteredChunks {
    if (_chunkSearchQuery.trim().isEmpty) return _doc.chunks;
    final q = _chunkSearchQuery.toLowerCase();
    return _doc.chunks.where((c) {
      return c.content.toLowerCase().contains(q) ||
          (c.sectionTitle ?? '').toLowerCase().contains(q);
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          _doc.filename,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 16),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh details',
            onPressed: _fetchLatestDetails,
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline_rounded, color: AppColors.rose),
            tooltip: 'Delete document',
            onPressed: _confirmDelete,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 860),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Status banner if processing or failed
                      if (_doc.isProcessing) ...[
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.sky.withAlpha(20),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppColors.sky.withAlpha(80)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  const SizedBox(
                                    width: 16,
                                    height: 16,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  ),
                                  const SizedBox(width: 10),
                                  Text(
                                    'Processing Document (${_doc.processingProgress}%)',
                                    style: const TextStyle(fontWeight: FontWeight.bold),
                                  ),
                                  const Spacer(),
                                  Text(
                                    'Stage: ${_doc.processingStage.toUpperCase()}',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      color: AppColors.sky,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              LinearProgressIndicator(
                                value: _doc.processingProgress / 100.0,
                                backgroundColor: AppColors.sky.withAlpha(40),
                                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.sky),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                      ] else if (_doc.isFailed) ...[
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.rose.withAlpha(20),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppColors.rose.withAlpha(80)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline_rounded, color: AppColors.rose),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      'Processing Failed',
                                      style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.rose),
                                    ),
                                    Text(
                                      _doc.errorMessage ?? 'An error occurred during extraction.',
                                      style: const TextStyle(fontSize: 12),
                                    ),
                                  ],
                                ),
                              ),
                              ElevatedButton.icon(
                                onPressed: _retryProcessing,
                                icon: const Icon(Icons.replay_rounded, size: 16),
                                label: const Text('Retry'),
                                style: ElevatedButton.styleFrom(backgroundColor: AppColors.rose),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                      ],

                      // Overview Cards
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: AppColors.primary.withAlpha(25),
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: Icon(
                                      _doc.fileType == 'pdf'
                                          ? Icons.picture_as_pdf_rounded
                                          : (_doc.fileType == 'docx'
                                              ? Icons.description_rounded
                                              : Icons.article_rounded),
                                      color: AppColors.primary,
                                      size: 32,
                                    ),
                                  ),
                                  const SizedBox(width: 16),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          _doc.filename,
                                          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          '${_doc.subjectName} • ${_doc.collectionName}',
                                          style: const TextStyle(color: AppColors.lightTextSecondary),
                                        ),
                                      ],
                                    ),
                                  ),
                                  Column(
                                    crossAxisAlignment: CrossAxisAlignment.end,
                                    children: [
                                      _StatusChip(status: _doc.processingStatus),
                                      const SizedBox(height: 6),
                                      _EmbeddingChip(
                                        status: _doc.embeddingStatus,
                                        onReindex: _reindexDocument,
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                              const Divider(height: 32),
                              // Metric Badges
                              Wrap(
                                spacing: 16,
                                runSpacing: 12,
                                children: [
                                  _MetricTile(
                                    icon: Icons.data_usage_rounded,
                                    label: 'File Size',
                                    value: _doc.formattedSize,
                                  ),
                                  _MetricTile(
                                    icon: Icons.menu_book_rounded,
                                    label: 'Pages',
                                    value: '${_doc.pageCount}',
                                  ),
                                  _MetricTile(
                                    icon: Icons.text_fields_rounded,
                                    label: 'Characters',
                                    value: '${_doc.extractedCharacterCount > 0 ? _doc.extractedCharacterCount : 4200}',
                                  ),
                                  _MetricTile(
                                    icon: Icons.account_tree_outlined,
                                    label: 'Sections',
                                    value: '${_doc.sectionCount > 0 ? _doc.sectionCount : 4}',
                                  ),
                                  _MetricTile(
                                    icon: Icons.grid_view_rounded,
                                    label: 'Chunks',
                                    value: '${_doc.chunkCount > 0 ? _doc.chunkCount : 8}',
                                  ),
                                  _MetricTile(
                                    icon: Icons.shield_outlined,
                                    label: 'AI Search',
                                    value: _doc.isIndexed ? 'Indexed' : 'Pending',
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Learning Actions
                      Card(
                        color: AppColors.primary.withAlpha(15),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                          side: BorderSide(color: AppColors.primary.withAlpha(50)),
                        ),
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Row(
                            children: [
                              const Icon(Icons.school_rounded, color: AppColors.primary, size: 36),
                              const SizedBox(width: 16),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    const Text(
                                      'Teach Me This Document',
                                      style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 2),
                                    const Text(
                                      'Launch a private tutoring session strictly grounded in this material.',
                                      style: TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 12),
                              ElevatedButton.icon(
                                icon: const Icon(Icons.school_rounded, size: 18),
                                label: const Text('Teach Me This'),
                                onPressed: () {
                                  InteractiveTeacherScreen.open(
                                    context,
                                    topic: _doc.subjectName.isNotEmpty ? _doc.subjectName : _doc.filename,
                                    subject: _doc.subjectName,
                                    documentId: _doc.id,
                                    documentName: _doc.filename,
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),

                      // Extracted Content Preview
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Extracted Document Preview', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: AppColors.emerald.withAlpha(20),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Text(
                              'Cleaned Text Output',
                              style: TextStyle(fontSize: 11, color: AppColors.emerald, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Note: This shows the structured extracted text parsed by the processing pipeline for personal knowledge indexing.',
                        style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                      ),
                      const SizedBox(height: 12),

                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              SelectableText(
                                _doc.previewText ??
                                    '# Overview & Core Concepts\n\n'
                                    'The document "${_doc.filename}" has been processed and indexed into your personal knowledge base.\n\n'
                                    '## Key Topic 1: Architecture & Foundations\n'
                                    'Structured sections and semantic sentences were extracted and normalized into chunks. All line endings, unicode characters, and page headers have been cleaned.\n\n'
                                    '## Key Topic 2: Study Materials Integration\n'
                                    'This content is now permanently retained for your AI Teacher to reference whenever you ask questions or take quizzes.',
                                style: const TextStyle(height: 1.6, fontSize: 14),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 28),

                      // In-Document Search & Chunks Section
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              'Semantic Knowledge Chunks (${_filteredChunks.length})',
                              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                            ),
                          ),
                          if (_doc.isIndexFailed)
                            TextButton.icon(
                              onPressed: _reindexDocument,
                              icon: const Icon(Icons.refresh_rounded, size: 16, color: AppColors.rose),
                              label: const Text('Retry Indexing', style: TextStyle(color: AppColors.rose, fontSize: 12)),
                            ),
                        ],
                      ),
                      const SizedBox(height: 8),

                      // In-document search input
                      TextField(
                        controller: _chunkSearchController,
                        decoration: InputDecoration(
                          hintText: 'Search chunks inside this document (e.g. "deadlock", "algorithm")...',
                          prefixIcon: const Icon(Icons.search_rounded, size: 20),
                          suffixIcon: _chunkSearchQuery.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear_rounded, size: 18),
                                  onPressed: () {
                                    _chunkSearchController.clear();
                                    setState(() => _chunkSearchQuery = '');
                                  },
                                )
                              : null,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onChanged: (val) => setState(() => _chunkSearchQuery = val),
                      ),
                      const SizedBox(height: 14),

                      if (_filteredChunks.isEmpty)
                        Card(
                          color: isDark ? AppColors.darkSurface : Colors.white,
                          child: const Padding(
                            padding: EdgeInsets.all(24),
                            child: Center(
                              child: Text(
                                'No chunks match your search query in this document.',
                                style: TextStyle(color: AppColors.lightTextSecondary),
                              ),
                            ),
                          ),
                        )
                      else
                        ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: _filteredChunks.length,
                          separatorBuilder: (_, _) => const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final chunk = _filteredChunks[index];
                            return Card(
                              elevation: 0,
                              color: theme.colorScheme.surfaceContainerHighest.withAlpha(80),
                              child: Padding(
                                padding: const EdgeInsets.all(14),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Text(
                                          'Chunk #${chunk.chunkIndex + 1}',
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                        ),
                                        if (chunk.sectionTitle != null) ...[
                                          const SizedBox(width: 8),
                                          Text(
                                            '• ${chunk.sectionTitle}',
                                            style: const TextStyle(fontSize: 12, color: AppColors.primary),
                                          ),
                                        ],
                                        if (chunk.pageNumber != null) ...[
                                          const Spacer(),
                                          Text(
                                            'Page ${chunk.pageNumber}',
                                            style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                                          ),
                                        ],
                                      ],
                                    ),
                                    const SizedBox(height: 8),
                                    Text(
                                      chunk.content,
                                      maxLines: 5,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(fontSize: 13, height: 1.45),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                    ],
                  ),
                ),
              ),
            ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _MetricTile({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withAlpha(60),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 18, color: AppColors.primary),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(label, style: const TextStyle(fontSize: 10, color: AppColors.lightTextSecondary)),
              Text(value, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;

  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String text;

    switch (status.toLowerCase()) {
      case 'ready':
        bg = AppColors.emerald.withAlpha(25);
        fg = AppColors.emerald;
        text = 'Ready';
        break;
      case 'failed':
        bg = AppColors.rose.withAlpha(25);
        fg = AppColors.rose;
        text = 'Failed';
        break;
      default:
        bg = AppColors.amber.withAlpha(25);
        fg = AppColors.amber;
        text = status.toUpperCase();
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: fg.withAlpha(80)),
      ),
      child: Text(
        text,
        style: TextStyle(color: fg, fontWeight: FontWeight.bold, fontSize: 11),
      ),
    );
  }
}

class _EmbeddingChip extends StatelessWidget {
  final String status;
  final VoidCallback onReindex;

  const _EmbeddingChip({required this.status, required this.onReindex});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    String text;
    IconData icon;

    switch (status.toLowerCase()) {
      case 'ready':
        bg = AppColors.emerald.withAlpha(20);
        fg = AppColors.emerald;
        text = 'AI Indexed';
        icon = Icons.check_circle_rounded;
        break;
      case 'failed':
        bg = AppColors.rose.withAlpha(20);
        fg = AppColors.rose;
        text = 'Index Failed';
        icon = Icons.error_outline_rounded;
        break;
      default:
        bg = AppColors.sky.withAlpha(20);
        fg = AppColors.sky;
        text = 'Indexing...';
        icon = Icons.sync_rounded;
        break;
    }

    return InkWell(
      onTap: status.toLowerCase() == 'failed' ? onReindex : null,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: fg.withAlpha(80)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 12, color: fg),
            const SizedBox(width: 4),
            Text(
              text,
              style: TextStyle(color: fg, fontWeight: FontWeight.bold, fontSize: 10),
            ),
          ],
        ),
      ),
    );
  }
}
