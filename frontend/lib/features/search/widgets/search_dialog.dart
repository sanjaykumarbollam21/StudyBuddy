import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../dashboard/screens/tutor_sheet.dart';
import '../../documents/models/document_model.dart';
import '../../documents/screens/document_detail_screen.dart';
import '../models/search_model.dart';
import '../services/search_api_service.dart';

class KnowledgeSearchDialog extends StatefulWidget {
  final List<DocumentItem> availableDocuments;
  final String? initialSubject;
  final String? initialCollection;
  final String? scopedDocumentId;

  const KnowledgeSearchDialog({
    super.key,
    this.availableDocuments = const [],
    this.initialSubject,
    this.initialCollection,
    this.scopedDocumentId,
  });

  static void show(
    BuildContext context, {
    List<DocumentItem> availableDocuments = const [],
    String? initialSubject,
    String? initialCollection,
    String? scopedDocumentId,
  }) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => KnowledgeSearchDialog(
        availableDocuments: availableDocuments,
        initialSubject: initialSubject,
        initialCollection: initialCollection,
        scopedDocumentId: scopedDocumentId,
      ),
    );
  }

  @override
  State<KnowledgeSearchDialog> createState() => _KnowledgeSearchDialogState();
}

class _KnowledgeSearchDialogState extends State<KnowledgeSearchDialog> {
  final TextEditingController _queryController = TextEditingController();
  final SearchApiService _searchService = SearchApiService();

  bool _isSearching = false;
  String _selectedScope = 'All Materials'; // All Materials, Current Subject, Scoped Document
  List<SearchResultItem> _results = [];

  @override
  void initState() {
    super.initState();
    if (widget.scopedDocumentId != null) {
      _selectedScope = 'This Document';
    } else if (widget.initialSubject != null) {
      _selectedScope = widget.initialSubject!;
    }
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  Future<void> _executeSearch() async {
    final query = _queryController.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _isSearching = true;
    });

    List<String>? docIds;
    String? subject;

    if (widget.scopedDocumentId != null || _selectedScope == 'This Document') {
      if (widget.scopedDocumentId != null) {
        docIds = [widget.scopedDocumentId!];
      }
    } else if (_selectedScope != 'All Materials') {
      subject = _selectedScope;
    }

    try {
      final response = await _searchService.hybridSearch(
        query,
        topK: 8,
        documentIds: docIds,
        subject: subject,
      );

      if (!mounted) return;
      setState(() {
        _results = response.results;
        _isSearching = false;
      });
    } catch (_) {
      // Offline fallback: match locally across available documents
      if (!mounted) return;
      final qLower = query.toLowerCase();
      final localResults = <SearchResultItem>[];

      for (final doc in widget.availableDocuments) {
        if (docIds != null && !docIds.contains(doc.id)) continue;
        if (subject != null && doc.subjectName != subject) continue;

        for (final chunk in doc.chunks) {
          if (chunk.content.toLowerCase().contains(qLower)) {
            localResults.add(
              SearchResultItem(
                chunkId: chunk.id,
                documentId: doc.id,
                documentName: doc.filename,
                content: chunk.content,
                pageNumber: chunk.pageNumber,
                sectionTitle: chunk.sectionTitle,
                similarity: 0.88,
                scoreType: 'keyword',
              ),
            );
          }
        }

        // If preview contains query
        if (localResults.isEmpty && (doc.previewText ?? '').toLowerCase().contains(qLower)) {
          localResults.add(
            SearchResultItem(
              chunkId: '${doc.id}-preview',
              documentId: doc.id,
              documentName: doc.filename,
              content: doc.previewText!,
              pageNumber: 1,
              sectionTitle: 'Overview',
              similarity: 0.82,
              scoreType: 'hybrid',
            ),
          );
        }
      }

      setState(() {
        _results = localResults;
        _isSearching = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final viewInsets = MediaQuery.of(context).viewInsets;

    return Container(
      height: MediaQuery.of(context).size.height * 0.88,
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Column(
        children: [
          // Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(
                  color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                ),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withAlpha(25),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.saved_search_rounded, color: AppColors.primary, size: 22),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Search Knowledge Base',
                        style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                      Text(
                        'Semantic + Keyword Hybrid Retrieval',
                        style: TextStyle(color: AppColors.emerald, fontSize: 11, fontWeight: FontWeight.w600),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close_rounded),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
          ),

          // Search Input Bar
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _queryController,
                    autofocus: true,
                    decoration: InputDecoration(
                      hintText: 'Search concepts, e.g. "virtual memory", "deadlock"...',
                      prefixIcon: const Icon(Icons.search_rounded),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    onSubmitted: (_) => _executeSearch(),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _isSearching ? null : _executeSearch,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
                  ),
                  child: _isSearching
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Search'),
                ),
              ],
            ),
          ),

          // Scope Filter Chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 6),
            child: Row(
              children: [
                ChoiceChip(
                  label: const Text('All Materials'),
                  selected: _selectedScope == 'All Materials',
                  onSelected: (_) => setState(() => _selectedScope = 'All Materials'),
                ),
                if (widget.scopedDocumentId != null) ...[
                  const SizedBox(width: 8),
                  ChoiceChip(
                    label: const Text('This Document'),
                    selected: _selectedScope == 'This Document',
                    onSelected: (_) => setState(() => _selectedScope = 'This Document'),
                  ),
                ],
                ...{
                  for (final doc in widget.availableDocuments) doc.subjectName
                }.map((sub) => Padding(
                      padding: const EdgeInsets.only(left: 8),
                      child: ChoiceChip(
                        label: Text(sub),
                        selected: _selectedScope == sub,
                        onSelected: (_) => setState(() => _selectedScope = sub),
                      ),
                    )),
              ],
            ),
          ),
          const Divider(height: 16),

          // Search Results List
          Expanded(
            child: _isSearching
                ? const Center(child: CircularProgressIndicator())
                : _results.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(32),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.auto_stories_outlined,
                                size: 52,
                                color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                              ),
                              const SizedBox(height: 14),
                              Text(
                                _queryController.text.isEmpty
                                    ? 'Search through your saved textbooks and notes'
                                    : 'No matching study material found',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                _queryController.text.isEmpty
                                    ? 'Try technical terms like "CPU scheduling", "relational algebra", or "concurrency".'
                                    : 'Check that the document is indexed or try different keywords.',
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      )
                    : ListView.separated(
                        padding: EdgeInsets.fromLTRB(18, 8, 18, 18 + viewInsets.bottom),
                        itemCount: _results.length,
                        separatorBuilder: (_, _) => const SizedBox(height: 10),
                        itemBuilder: (context, index) {
                          final item = _results[index];
                          final matchedDoc = widget.availableDocuments.firstWhere(
                            (d) => d.id == item.documentId,
                            orElse: () => DocumentItem(
                              id: item.documentId,
                              filename: item.documentName,
                              fileType: 'pdf',
                              fileSizeBytes: 1024,
                              pageCount: item.pageNumber ?? 1,
                              createdAt: DateTime.now(),
                            ),
                          );

                          return Card(
                            elevation: 0,
                            color: isDark ? AppColors.darkSurface : Colors.white,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(14),
                              side: BorderSide(
                                color: isDark ? AppColors.darkBorder : AppColors.lightBorder,
                              ),
                            ),
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.all(6),
                                        decoration: BoxDecoration(
                                          color: AppColors.primary.withAlpha(20),
                                          borderRadius: BorderRadius.circular(8),
                                        ),
                                        child: const Icon(Icons.description_rounded, size: 16, color: AppColors.primary),
                                      ),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          item.documentName,
                                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                        decoration: BoxDecoration(
                                          color: AppColors.emerald.withAlpha(20),
                                          borderRadius: BorderRadius.circular(10),
                                        ),
                                        child: Text(
                                          '${(item.similarity * 100).toInt()}% Match',
                                          style: const TextStyle(
                                            color: AppColors.emerald,
                                            fontWeight: FontWeight.bold,
                                            fontSize: 11,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  if (item.pageNumber != null || item.sectionTitle != null) ...[
                                    const SizedBox(height: 6),
                                    Text(
                                      '${item.pageNumber != null ? "Page ${item.pageNumber}" : ""} ${item.sectionTitle != null ? "• ${item.sectionTitle}" : ""}'
                                          .trim(),
                                      style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600,
                                        color: isDark ? AppColors.darkTextSecondary : AppColors.lightTextSecondary,
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 10),
                                  Text(
                                    item.content,
                                    maxLines: 4,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(fontSize: 13, height: 1.45),
                                  ),
                                  const SizedBox(height: 12),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.end,
                                    children: [
                                      OutlinedButton.icon(
                                        onPressed: () {
                                          Navigator.of(context).pop();
                                          Navigator.of(context).push(
                                            MaterialPageRoute(
                                              builder: (_) => DocumentDetailScreen(document: matchedDoc),
                                            ),
                                          );
                                        },
                                        icon: const Icon(Icons.visibility_outlined, size: 16),
                                        label: const Text('View Document', style: TextStyle(fontSize: 12)),
                                      ),
                                      const SizedBox(width: 8),
                                      ElevatedButton.icon(
                                        onPressed: () {
                                          Navigator.of(context).pop();
                                          TutorSheet.show(
                                            context,
                                            initialPrompt: 'Teach me about "${_queryController.text}" based on my material "${item.documentName}".',
                                            scopedDocumentId: item.documentId,
                                            scopedDocumentName: item.documentName,
                                          );
                                        },
                                        icon: const Icon(Icons.school_rounded, size: 16),
                                        label: const Text('Teach From This', style: TextStyle(fontSize: 12)),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
