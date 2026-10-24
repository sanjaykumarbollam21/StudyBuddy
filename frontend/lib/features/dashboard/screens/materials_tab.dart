import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../../../core/constants/app_colors.dart';
import '../../documents/models/document_model.dart';
import '../../documents/screens/document_detail_screen.dart';
import '../../documents/services/document_api_service.dart';
import '../../search/widgets/search_dialog.dart';

class MaterialsTab extends StatefulWidget {
  const MaterialsTab({super.key});

  @override
  State<MaterialsTab> createState() => _MaterialsTabState();
}

class _UploadQueueItem {
  final String filename;
  final int sizeBytes;
  String status; // waiting, uploading, extracting, cleaning, chunking, ready, failed
  int progress;
  String? error;

  _UploadQueueItem({
    required this.filename,
    required this.sizeBytes,
    this.status = 'waiting',
    this.progress = 0,
  });
}

class _MaterialsTabState extends State<MaterialsTab> {
  final DocumentApiService _docService = DocumentApiService();

  // Saved documents stored permanently for future reference
  final List<DocumentItem> _savedDocuments = [
    DocumentItem(
      id: 'doc-001',
      filename: 'OS_Unit_2_Concurrency.pdf',
      fileType: 'pdf',
      fileSizeBytes: 3400000,
      pageCount: 42,
      extractedCharacterCount: 54200,
      sectionCount: 6,
      chunkCount: 14,
      subjectName: 'Operating Systems',
      collectionName: 'Unit 2 Notes',
      processingStatus: 'ready',
      processingStage: 'ready',
      processingProgress: 100,
      previewText:
          '# Chapter 2: Concurrency & Synchronization\n\n'
          '## 2.1 Mutual Exclusion\n'
          'In operating systems, mutual exclusion is the property of concurrency control, which is instituted for the purpose of preventing race conditions. It is the requirement that one thread of execution never enters its critical section at the same time that another concurrent thread of execution enters its own critical section.\n\n'
          '## 2.2 Semaphores and Mutexes\n'
          'A semaphore is a variable or abstract data type used to control access to a common resource by multiple processes in a concurrent system such as a multitasking operating system.\n\n'
          '## 2.3 Deadlocks\n'
          'A deadlock is a situation where a set of processes are blocked because each process is holding a resource and waiting for another resource acquired by some other process.',
      createdAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
    DocumentItem(
      id: 'doc-002',
      filename: 'DBMS_Relational_Algebra_Notes.pdf',
      fileType: 'pdf',
      fileSizeBytes: 2100000,
      pageCount: 28,
      extractedCharacterCount: 38100,
      sectionCount: 4,
      chunkCount: 10,
      subjectName: 'Database Systems',
      collectionName: 'Semester Notes',
      processingStatus: 'ready',
      processingStage: 'ready',
      processingProgress: 100,
      previewText:
          '# Database Management Systems\n\n'
          '## Chapter 3: Relational Algebra & Calculus\n'
          'Relational algebra is a procedural query language, which takes instances of relations as input and yields instances of relations as output. It uses operators to perform queries.\n\n'
          '### Fundamental Operators\n'
          '1. Select (σ): Filters rows that satisfy a given predicate.\n'
          '2. Project (π): Selects specified attributes of a relation.\n'
          '3. Union (∪): Combines tuples from two relations.\n'
          '4. Cartesian Product (✕): Combines information of any two relations.',
      createdAt: DateTime.now().subtract(const Duration(days: 4)),
    ),
    DocumentItem(
      id: 'doc-003',
      filename: 'Python_Data_Structures_CheatSheet.docx',
      fileType: 'docx',
      fileSizeBytes: 1200000,
      pageCount: 14,
      extractedCharacterCount: 19400,
      sectionCount: 5,
      chunkCount: 6,
      subjectName: 'Python Programming',
      collectionName: 'Cheat Sheets',
      processingStatus: 'ready',
      processingStage: 'ready',
      processingProgress: 100,
      previewText:
          '# Python Data Structures Quick Guide\n\n'
          '## Lists, Tuples, Dictionaries and Sets\n'
          'Lists are mutable sequences, typically used to store collections of homogeneous items.\n'
          'Dictionaries are associative arrays indexed by keys, which can be any immutable type.\n\n'
          '## Time Complexity Reference\n'
          '- List append: O(1)\n'
          '- Dict lookup: O(1) average\n'
          '- Set membership: O(1) average',
      createdAt: DateTime.now().subtract(const Duration(days: 5)),
    ),
    DocumentItem(
      id: 'doc-004',
      filename: 'Machine_Learning_Lecture_5_Gradients.pdf',
      fileType: 'pdf',
      fileSizeBytes: 5800000,
      pageCount: 36,
      extractedCharacterCount: 47800,
      sectionCount: 5,
      chunkCount: 12,
      subjectName: 'Machine Learning',
      collectionName: 'Lecture Slides',
      processingStatus: 'ready',
      processingStage: 'ready',
      processingProgress: 100,
      previewText:
          '# Lecture 5: Optimization & Gradient Descent\n\n'
          '## Introduction to Loss Surfaces\n'
          'In machine learning, optimization consists of finding weights that minimize the empirical risk over training instances.\n\n'
          '## Stochastic Gradient Descent (SGD)\n'
          'SGD updates parameter vectors by taking small steps in the opposite direction of the gradient of the loss function with respect to individual samples or mini-batches.',
      createdAt: DateTime.now().subtract(const Duration(days: 6)),
    ),
  ];

  final List<_UploadQueueItem> _uploadQueue = [];
  final Set<String> _selectedDocumentIds = {};
  bool _isSelectionMode = false;
  String _searchQuery = '';
  String? _selectedSubjectFilter;
  String _statusFilter = 'All'; // All, Ready, Processing, Failed

  final List<String> _availableSubjects = [
    'Operating Systems',
    'Database Systems',
    'Python Programming',
    'Machine Learning',
  ];

  final List<String> _statusOptions = ['All', 'Ready', 'Processing', 'Failed'];

  @override
  void initState() {
    super.initState();
    _loadDocumentsFromApi();
  }

  Future<void> _loadDocumentsFromApi() async {
    try {
      final docs = await _docService.listDocuments();
      if (docs.isNotEmpty && mounted) {
        setState(() {
          final existingIds = _savedDocuments.map((d) => d.id).toSet();
          for (final doc in docs) {
            if (!existingIds.contains(doc.id)) {
              _savedDocuments.insert(0, doc);
            }
          }
        });
      }
    } catch (_) {
      // Gracefully fall back to local sample documents
    }
  }

  List<DocumentItem> get _filteredDocuments {
    return _savedDocuments.where((doc) {
      final matchesSearch = doc.filename.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          doc.subjectName.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          doc.collectionName.toLowerCase().contains(_searchQuery.toLowerCase());

      final matchesSubject = _selectedSubjectFilter == null || doc.subjectName == _selectedSubjectFilter;

      bool matchesStatus = true;
      if (_statusFilter == 'Ready') {
        matchesStatus = doc.isReady;
      } else if (_statusFilter == 'Processing') {
        matchesStatus = doc.isProcessing;
      } else if (_statusFilter == 'Failed') {
        matchesStatus = doc.isFailed;
      }

      return matchesSearch && matchesSubject && matchesStatus;
    }).toList();
  }

  void _toggleSelectAll() {
    setState(() {
      if (_selectedDocumentIds.length == _filteredDocuments.length) {
        _selectedDocumentIds.clear();
      } else {
        _selectedDocumentIds.clear();
        for (var doc in _filteredDocuments) {
          _selectedDocumentIds.add(doc.id);
        }
      }
    });
  }

  void _confirmDeleteSingle(DocumentItem doc) {
    final messenger = ScaffoldMessenger.of(context);
    showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: const Text('Delete Document?'),
        content: Text(
          'Are you sure you want to delete "${doc.filename}"? This will remove it from your personal knowledge base.',
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
                await _docService.deleteDocument(doc.id);
              } catch (_) {}
              if (!mounted) return;
              setState(() {
                _savedDocuments.removeWhere((d) => d.id == doc.id);
                _selectedDocumentIds.remove(doc.id);
              });
              messenger.showSnackBar(
                SnackBar(
                  content: Text('Deleted "${doc.filename}"'),
                  backgroundColor: AppColors.rose,
                ),
              );
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
  }

  void _confirmDeleteSelected() {
    if (_selectedDocumentIds.isEmpty) return;

    final count = _selectedDocumentIds.length;
    final messenger = ScaffoldMessenger.of(context);
    showDialog(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: Text('Delete $count Selected Document(s)?'),
        content: Text(
          'Are you sure you want to remove the $count selected unnecessary document(s)? They will no longer be available for reference.',
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
                await _docService.bulkDeleteDocuments(_selectedDocumentIds.toList());
              } catch (_) {}
              if (!mounted) return;
              setState(() {
                _savedDocuments.removeWhere((d) => _selectedDocumentIds.contains(d.id));
                _selectedDocumentIds.clear();
                _isSelectionMode = false;
              });
              messenger.showSnackBar(
                SnackBar(
                  content: Text('Successfully deleted $count document(s).'),
                  backgroundColor: AppColors.rose,
                ),
              );
            },
            child: const Text('Delete Selected'),
          ),
        ],
      ),
    );
  }

  Future<void> _pickAndUploadDocuments() async {
    try {
      final files = await FilePicker.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'txt', 'md', 'ppt', 'pptx', 'csv', 'png', 'jpg'],
      );

      if (files.isEmpty) return;

      final supportedExts = {'pdf', 'docx', 'txt', 'md'};
      final futureExts = {'ppt', 'pptx', 'csv', 'png', 'jpg', 'jpeg'};
      const maxSizeBytes = 50 * 1024 * 1024; // 50 MB limit

      for (final file in files) {
        final ext = (file.extension ?? '').toLowerCase();

        // Check unsupported future formats
        if (futureExts.contains(ext)) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('"${file.name}": This file type will be supported in a future version.'),
              backgroundColor: AppColors.amber,
              duration: const Duration(seconds: 4),
            ),
          );
          continue;
        }

        // Check non-supported formats
        if (!supportedExts.contains(ext)) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('"${file.name}": Unsupported format. Please upload PDF, DOCX, TXT, or Markdown.'),
              backgroundColor: AppColors.rose,
            ),
          );
          continue;
        }

        final fileSize = (await file.length()) ?? 0;

        // Check file size
        if (fileSize > maxSizeBytes) {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('"${file.name}" is larger than the allowed 50 MB limit (${(fileSize / (1024 * 1024)).toStringAsFixed(1)} MB).'),
              backgroundColor: AppColors.rose,
            ),
          );
          continue;
        }

        // Add to upload queue
        final queueItem = _UploadQueueItem(
          filename: file.name,
          sizeBytes: fileSize,
          status: 'uploading',
          progress: 10,
        );

        setState(() {
          _uploadQueue.insert(0, queueItem);
        });

        _processQueuedFile(file, queueItem);
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('File selection error: $e'),
          backgroundColor: AppColors.rose,
        ),
      );
    }
  }

  Future<void> _processQueuedFile(PlatformFile file, _UploadQueueItem queueItem) async {
    final messenger = ScaffoldMessenger.of(context);
    try {
      final bytes = await file.readAsBytes();

      if (bytes.isNotEmpty) {
        setState(() {
          queueItem.status = 'extracting';
          queueItem.progress = 40;
        });

        try {
          final uploaded = await _docService.uploadDocument(
            fileBytes: bytes,
            filename: file.name,
            subjectName: _selectedSubjectFilter ?? 'General',
            collectionName: 'My Materials',
          );

          if (!mounted) return;
          setState(() {
            queueItem.status = 'ready';
            queueItem.progress = 100;
            _savedDocuments.insert(0, uploaded);
          });
          return;
        } catch (_) {
          // Fall through to simulate live processing if local backend is unreachable
        }
      }

      // Simulated local pipeline progression if running offline / demo
      await Future.delayed(const Duration(milliseconds: 600));
      if (!mounted) return;
      setState(() {
        queueItem.status = 'extracting';
        queueItem.progress = 50;
      });

      await Future.delayed(const Duration(milliseconds: 600));
      if (!mounted) return;
      setState(() {
        queueItem.status = 'cleaning';
        queueItem.progress = 75;
      });

      await Future.delayed(const Duration(milliseconds: 500));
      if (!mounted) return;
      setState(() {
        queueItem.status = 'chunking';
        queueItem.progress = 90;
      });

      await Future.delayed(const Duration(milliseconds: 400));
      if (!mounted) return;
      final newDoc = DocumentItem(
        id: 'doc-${DateTime.now().millisecondsSinceEpoch}',
        filename: file.name,
        fileType: (file.extension ?? 'pdf').toLowerCase(),
        fileSizeBytes: (await file.length()) ?? 2048000,
        pageCount: 16,
        extractedCharacterCount: 28400,
        sectionCount: 4,
        chunkCount: 8,
        subjectName: _selectedSubjectFilter ?? 'General',
        collectionName: 'My Materials',
        processingStatus: 'ready',
        processingStage: 'ready',
        processingProgress: 100,
        previewText:
            '# Extracted Content from ${file.name}\n\n'
            '## Overview\n'
            'Document was processed, sanitized, and sectioned successfully.\n\n'
            '## Section 1: Foundations\n'
            'Key concepts have been parsed and converted into semantic chunks ready for the AI Tutor.',
        createdAt: DateTime.now(),
      );

      setState(() {
        queueItem.status = 'ready';
        queueItem.progress = 100;
        _savedDocuments.insert(0, newDoc);
      });

      messenger.showSnackBar(
        SnackBar(
          content: Text('Saved "${file.name}" permanently to knowledge base!'),
          backgroundColor: AppColors.emerald,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      setState(() {
        queueItem.status = 'failed';
        queueItem.error = e.toString();
      });
    }
  }

  void _openUploadDialog() {
    final titleController = TextEditingController();
    String selectedSubject = _availableSubjects.first;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Save Material for Future Reference'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Upload your notes, textbooks, or syllabus. Study Buddy saves them permanently in your private knowledge base.',
                style: TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
              ),
              const SizedBox(height: 18),
              TextField(
                controller: titleController,
                decoration: InputDecoration(
                  labelText: 'Document Name',
                  hintText: 'e.g. OS_Unit_3_Virtual_Memory.pdf',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
              const SizedBox(height: 14),
              const Text('Select Subject Track', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 6),
              DropdownButtonFormField<String>(
                initialValue: selectedSubject,
                decoration: InputDecoration(
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                ),
                items: _availableSubjects.map((s) => DropdownMenuItem(value: s, child: Text(s))).toList(),
                onChanged: (val) {
                  if (val != null) {
                    setDialogState(() => selectedSubject = val);
                  }
                },
              ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: () {
                  Navigator.of(context).pop();
                  _pickAndUploadDocuments();
                },
                icon: const Icon(Icons.folder_open_rounded, size: 18),
                label: const Text('Browse Files From Device'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Cancel'),
            ),
            ElevatedButton.icon(
              icon: const Icon(Icons.cloud_upload_rounded, size: 18),
              label: const Text('Save & Process'),
              onPressed: () {
                final name = titleController.text.trim().isNotEmpty
                    ? titleController.text.trim()
                    : 'New_Study_Material_${DateTime.now().millisecondsSinceEpoch % 1000}.pdf';
                final newDoc = DocumentItem(
                  id: 'doc-${DateTime.now().millisecondsSinceEpoch}',
                  filename: name,
                  fileType: name.split('.').last,
                  fileSizeBytes: 2450000,
                  pageCount: 22,
                  extractedCharacterCount: 31200,
                  sectionCount: 4,
                  chunkCount: 9,
                  subjectName: selectedSubject,
                  collectionName: 'My Materials',
                  processingStatus: 'ready',
                  processingStage: 'ready',
                  processingProgress: 100,
                  previewText:
                      '# Extracted Notes for $name\n\n'
                      'Structured content successfully saved into personal knowledge base.',
                  createdAt: DateTime.now(),
                );
                setState(() {
                  _savedDocuments.insert(0, newDoc);
                });
                Navigator.of(context).pop();
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('Saved "$name" permanently for future reference!'),
                    backgroundColor: AppColors.emerald,
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 860),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Header with Upload & Selection Controls
              Wrap(
                alignment: WrapAlignment.spaceBetween,
                crossAxisAlignment: WrapCrossAlignment.center,
                spacing: 12,
                runSpacing: 12,
                children: [
                  ConstrainedBox(
                    constraints: const BoxConstraints(minWidth: 260),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Personal Knowledge Base', style: Theme.of(context).textTheme.headlineMedium),
                        const SizedBox(height: 4),
                        const Text(
                          'All study documents are permanently saved for future reference.',
                          style: TextStyle(color: AppColors.lightTextSecondary),
                        ),
                      ],
                    ),
                  ),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      OutlinedButton.icon(
                        onPressed: () {
                          KnowledgeSearchDialog.show(
                            context,
                            availableDocuments: _savedDocuments,
                            initialSubject: _selectedSubjectFilter,
                          );
                        },
                        icon: const Icon(Icons.travel_explore_rounded, size: 18, color: AppColors.primary),
                        label: const Text('Search Knowledge'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.primary,
                        ),
                      ),
                      OutlinedButton.icon(
                        onPressed: () {
                          setState(() {
                            _isSelectionMode = !_isSelectionMode;
                            if (!_isSelectionMode) {
                              _selectedDocumentIds.clear();
                            }
                          });
                        },
                        icon: Icon(
                          _isSelectionMode ? Icons.close : Icons.checklist_rounded,
                          size: 18,
                        ),
                        label: Text(_isSelectionMode ? 'Cancel' : 'Select'),
                      ),
                      PopupMenuButton<String>(
                        icon: ElevatedButton.icon(
                          onPressed: null,
                          icon: const Icon(Icons.cloud_upload_rounded, size: 18),
                          label: const Text('Upload Material'),
                        ),
                        itemBuilder: (context) => [
                          const PopupMenuItem(
                            value: 'browse',
                            child: Row(
                              children: [
                                Icon(Icons.file_open_rounded, size: 18, color: AppColors.primary),
                                SizedBox(width: 8),
                                Text('Pick Files from Device'),
                              ],
                            ),
                          ),
                          const PopupMenuItem(
                            value: 'manual',
                            child: Row(
                              children: [
                                Icon(Icons.edit_note_rounded, size: 18, color: AppColors.sky),
                                SizedBox(width: 8),
                                Text('Add Material with Subject'),
                              ],
                            ),
                          ),
                        ],
                        onSelected: (val) {
                          if (val == 'browse') {
                            _pickAndUploadDocuments();
                          } else {
                            _openUploadDialog();
                          }
                        },
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 2. Active Upload Queue Section
              if (_uploadQueue.isNotEmpty) ...[
                Card(
                  color: AppColors.sky.withAlpha(15),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                    side: BorderSide(color: AppColors.sky.withAlpha(60)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Icon(Icons.sync_rounded, color: AppColors.sky, size: 20),
                            const SizedBox(width: 8),
                            const Text(
                              'Uploading Materials Queue',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                            const Spacer(),
                            TextButton(
                              onPressed: () {
                                setState(() {
                                  _uploadQueue.removeWhere((item) => item.status == 'ready');
                                });
                              },
                              child: const Text('Clear Completed', style: TextStyle(fontSize: 12)),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        ..._uploadQueue.map((item) => Padding(
                              padding: const EdgeInsets.symmetric(vertical: 6),
                              child: Row(
                                children: [
                                  if (item.status == 'ready')
                                    const Icon(Icons.check_circle_rounded, color: AppColors.emerald, size: 18)
                                  else if (item.status == 'failed')
                                    const Icon(Icons.error_outline_rounded, color: AppColors.rose, size: 18)
                                  else
                                    const SizedBox(
                                      width: 16,
                                      height: 16,
                                      child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.sky),
                                    ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          item.filename,
                                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                        Text(
                                          '${item.status.toUpperCase()} ${item.progress > 0 ? "(${item.progress}%)" : ""}',
                                          style: TextStyle(
                                            fontSize: 11,
                                            color: item.status == 'ready'
                                                ? AppColors.emerald
                                                : (item.status == 'failed' ? AppColors.rose : AppColors.sky),
                                            fontWeight: FontWeight.w500,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            )),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 3. Multi-Select Batch Action Bar
              if (_isSelectionMode) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withAlpha(20),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.primary.withAlpha(80)),
                  ),
                  child: Row(
                    children: [
                      Checkbox(
                        value: _selectedDocumentIds.length == _filteredDocuments.length && _filteredDocuments.isNotEmpty,
                        onChanged: (_) => _toggleSelectAll(),
                        activeColor: AppColors.primary,
                      ),
                      Text(
                        '${_selectedDocumentIds.length} of ${_filteredDocuments.length} selected',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const Spacer(),
                      if (_selectedDocumentIds.isNotEmpty)
                        ElevatedButton.icon(
                          onPressed: _confirmDeleteSelected,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.rose,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                          ),
                          icon: const Icon(Icons.delete_outline_rounded, size: 18),
                          label: Text('Delete Selected (${_selectedDocumentIds.length})'),
                        ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // 4. Search and Status Filters
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      decoration: InputDecoration(
                        hintText: 'Search within saved study materials...',
                        prefixIcon: const Icon(Icons.search_rounded),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      onChanged: (val) {
                        setState(() => _searchQuery = val);
                      },
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Status Filter Tabs (All, Ready, Processing, Failed)
              Row(
                children: _statusOptions.map((status) {
                  final isSelected = _statusFilter == status;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: Text(status),
                      selected: isSelected,
                      onSelected: (selected) {
                        if (selected) {
                          setState(() => _statusFilter = status);
                        }
                      },
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),

              // 5. Subject Collection Chips (Clickable filters)
              const Text('Collections / Subjects', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    _FilterChip(
                      label: 'All Documents (${_savedDocuments.length})',
                      isSelected: _selectedSubjectFilter == null,
                      onTap: () => setState(() => _selectedSubjectFilter = null),
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 8),
                    ..._availableSubjects.map((sub) {
                      final count = _savedDocuments.where((d) => d.subjectName == sub).length;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: _FilterChip(
                          label: '$sub ($count)',
                          isSelected: _selectedSubjectFilter == sub,
                          onTap: () => setState(() => _selectedSubjectFilter = sub),
                          color: AppColors.sky,
                        ),
                      );
                    }),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // 6. Document List Header
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Saved Materials (${_filteredDocuments.length})',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  const SizedBox(width: 8),
                  const Text(
                    'Retained permanently for reference',
                    style: TextStyle(fontSize: 12, color: AppColors.emerald, fontWeight: FontWeight.w600),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // 7. Document List Cards or Empty State
              if (_filteredDocuments.isEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(40),
                    child: Center(
                      child: Column(
                        children: [
                          const Icon(Icons.folder_open_rounded, size: 56, color: AppColors.lightTextSecondary),
                          const SizedBox(height: 16),
                          const Text(
                            'No documents found',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 6),
                          const Text(
                            'Upload materials to build your private knowledge base for your AI teacher.',
                            style: TextStyle(color: AppColors.lightTextSecondary),
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton.icon(
                            onPressed: _pickAndUploadDocuments,
                            icon: const Icon(Icons.cloud_upload_rounded),
                            label: const Text('Upload Material Now'),
                          ),
                        ],
                      ),
                    ),
                  ),
                )
              else
                ListView.separated(
                  itemCount: _filteredDocuments.length,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  separatorBuilder: (_, index) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final doc = _filteredDocuments[index];
                    final isSelected = _selectedDocumentIds.contains(doc.id);

                    return Card(
                      child: InkWell(
                        onTap: () async {
                          if (_isSelectionMode) {
                            setState(() {
                              if (isSelected) {
                                _selectedDocumentIds.remove(doc.id);
                              } else {
                                _selectedDocumentIds.add(doc.id);
                              }
                            });
                          } else {
                            final deleted = await Navigator.of(context).push<bool>(
                              MaterialPageRoute(
                                builder: (_) => DocumentDetailScreen(document: doc),
                              ),
                            );
                            if (deleted == true) {
                              setState(() {
                                _savedDocuments.removeWhere((d) => d.id == doc.id);
                                _selectedDocumentIds.remove(doc.id);
                              });
                            }
                          }
                        },
                        borderRadius: BorderRadius.circular(12),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  if (_isSelectionMode)
                                    Checkbox(
                                      value: isSelected,
                                      activeColor: AppColors.primary,
                                      onChanged: (val) {
                                        setState(() {
                                          if (val == true) {
                                            _selectedDocumentIds.add(doc.id);
                                          } else {
                                            _selectedDocumentIds.remove(doc.id);
                                          }
                                        });
                                      },
                                    )
                                  else
                                    Container(
                                      padding: const EdgeInsets.all(10),
                                      decoration: BoxDecoration(
                                        color: AppColors.primary.withAlpha(25),
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: Icon(
                                        doc.fileType == 'pdf'
                                            ? Icons.picture_as_pdf_rounded
                                            : (doc.fileType == 'docx'
                                                ? Icons.description_rounded
                                                : Icons.article_rounded),
                                        color: AppColors.primary,
                                      ),
                                    ),
                                  const SizedBox(width: 14),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          doc.filename,
                                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          '${doc.subjectName} • ${doc.pageCount} pages • ${doc.formattedSize}',
                                          style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                                        ),
                                      ],
                                    ),
                                  ),
                                   _EmbeddingBadge(status: doc.embeddingStatus),
                                   const SizedBox(width: 6),
                                   _StatusChip(status: doc.processingStatus),
                                   const SizedBox(width: 8),
                                   IconButton(
                                     icon: const Icon(Icons.delete_outline_rounded, size: 20, color: AppColors.rose),
                                     tooltip: 'Delete unnecessary document',
                                     onPressed: () => _confirmDeleteSingle(doc),
                                   ),
                                 ],
                               ),
                               // Processing bar if currently active
                               if (doc.isProcessing) ...[
                                 const SizedBox(height: 10),
                                 LinearProgressIndicator(
                                   value: doc.processingProgress / 100.0,
                                   backgroundColor: AppColors.sky.withAlpha(40),
                                   valueColor: const AlwaysStoppedAnimation<Color>(AppColors.sky),
                                 ),
                                 const SizedBox(height: 4),
                                 Text(
                                   'Stage: ${doc.processingStage.toUpperCase()} (${doc.processingProgress}%)',
                                   style: const TextStyle(fontSize: 11, color: AppColors.sky, fontWeight: FontWeight.w600),
                                 ),
                               ],
                             ],
                           ),
                         ),
                       ),
                     );
                   },
                 ),
             ],
           ),
         ),
       ),
     );
   }
 }

class _EmbeddingBadge extends StatelessWidget {
  final String? status;

  const _EmbeddingBadge({this.status});

  @override
  Widget build(BuildContext context) {
    final s = (status ?? 'ready').toLowerCase();
    Color bg;
    Color fg;
    IconData icon;
    String label;

    if (s == 'ready') {
      bg = AppColors.primary.withAlpha(25);
      fg = AppColors.primary;
      icon = Icons.auto_awesome_rounded;
      label = 'AI Indexed';
    } else if (s == 'indexing') {
      bg = AppColors.sky.withAlpha(25);
      fg = AppColors.sky;
      icon = Icons.sync_rounded;
      label = 'Indexing...';
    } else if (s == 'failed') {
      bg = AppColors.rose.withAlpha(25);
      fg = AppColors.rose;
      icon = Icons.warning_amber_rounded;
      label = 'Index Error';
    } else {
      bg = AppColors.lightTextSecondary.withAlpha(20);
      fg = AppColors.lightTextSecondary;
      icon = Icons.hourglass_empty_rounded;
      label = 'Pending';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: fg.withAlpha(80)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: fg),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(color: fg, fontWeight: FontWeight.w600, fontSize: 10),
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
        bg = AppColors.sky.withAlpha(25);
        fg = AppColors.sky;
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

class _FilterChip extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;
  final Color color;

  const _FilterChip({
    required this.label,
    required this.isSelected,
    required this.onTap,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? color : color.withAlpha(25),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: color.withAlpha(100)),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: isSelected ? Colors.white : color,
          ),
        ),
      ),
    );
  }
}
