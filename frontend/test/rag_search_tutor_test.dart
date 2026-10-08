import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/documents/models/document_model.dart';
import 'package:frontend/features/search/models/search_model.dart';
import 'package:frontend/features/tutor/models/tutor_model.dart';
import 'package:frontend/features/dashboard/screens/tutor_sheet.dart';
import 'package:frontend/features/search/widgets/search_dialog.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('Phase 3 Models Serialization & Status Getters', () {
    test('DocumentItem embedding status getters work correctly', () {
      final docReady = DocumentItem(
        id: 'doc-1',
        filename: 'OS_Concurrency.pdf',
        fileType: 'pdf',
        fileSizeBytes: 1024,
        pageCount: 10,
        extractedCharacterCount: 500,
        sectionCount: 2,
        chunkCount: 4,
        subjectName: 'Operating Systems',
        collectionName: 'Notes',
        processingStatus: 'ready',
        processingStage: 'ready',
        processingProgress: 100,
        embeddingStatus: 'ready',
        createdAt: DateTime.now(),
      );

      expect(docReady.isIndexed, isTrue);
      expect(docReady.isIndexing, isFalse);
      expect(docReady.isIndexFailed, isFalse);

      final json = docReady.toJson();
      expect(json['embedding_status'], equals('ready'));

      final docIndexing = DocumentItem(
        id: 'doc-2',
        filename: 'DBMS.pdf',
        fileType: 'pdf',
        fileSizeBytes: 1024,
        pageCount: 5,
        extractedCharacterCount: 200,
        sectionCount: 1,
        chunkCount: 2,
        subjectName: 'DBMS',
        collectionName: 'Notes',
        processingStatus: 'ready',
        processingStage: 'ready',
        processingProgress: 100,
        embeddingStatus: 'indexing',
        createdAt: DateTime.now(),
      );

      expect(docIndexing.isIndexed, isFalse);
      expect(docIndexing.isIndexing, isTrue);
      expect(docIndexing.isIndexFailed, isFalse);
    });

    test('SearchResultItem and SearchResponseModel serialize properly', () {
      final result = SearchResultItem(
        chunkId: 'chunk-123',
        documentId: 'doc-456',
        documentName: 'OS_Notes.pdf',
        pageNumber: 14,
        sectionTitle: 'Deadlocks',
        content: 'A deadlock condition requires mutual exclusion and hold-and-wait.',
        similarity: 0.88,
        scoreType: 'hybrid',
      );

      expect(result.similarityPercentage, equals('88%'));
      final json = result.toJson();
      final reconstructed = SearchResultItem.fromJson(json);
      expect(reconstructed.chunkId, equals('chunk-123'));
      expect(reconstructed.similarity, equals(0.88));

      final response = SearchResponseModel(
        query: 'deadlocks',
        totalResults: 1,
        results: [result],
      );
      expect(response.results.length, equals(1));
      expect(response.totalResults, equals(1));
    });

    test('TutorResponseModel with SourceCitationItem serializes properly', () {
      final citation = SourceCitationItem(
        chunkId: 'c-1',
        documentId: 'd-1',
        documentName: 'OS_Notes.pdf',
        pageNumber: 14,
        sectionTitle: 'Deadlocks',
        similarityScore: 0.92,
      );

      final tutorResp = TutorResponseModel(
        answer: 'Deadlocks occur when processes cycle on resources.',
        groundingMode: 'strict_materials',
        sources: [citation],
        contextUsed: true,
      );

      expect(tutorResp.sources.length, equals(1));
      expect(tutorResp.hasSources, isTrue);
      expect(tutorResp.sources.first.documentName, equals('OS_Notes.pdf'));
      expect(tutorResp.groundingMode, equals('strict_materials'));
    });
  });

  group('Phase 3 Widgets Tests', () {
    testWidgets('TutorSheet renders grounding selector and handles document scope', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: TutorSheet(
              scopedDocumentId: 'doc-001',
              scopedDocumentName: 'OS_Unit_2_Concurrency.pdf',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Scoped document badge check
      expect(find.textContaining('Teaching from: OS_Unit_2_Concurrency.pdf'), findsOneWidget);
      expect(find.text('Study Buddy AI Teacher'), findsOneWidget);

      // Verify Grounding Mode Selector exists
      expect(find.text('Materials + General'), findsOneWidget);

      // Enter query
      await tester.enterText(find.byType(TextField), 'Explain Semaphores');
      await tester.pump();

      expect(find.text('Explain Semaphores'), findsOneWidget);
    });

    testWidgets('KnowledgeSearchDialog opens and renders search UI', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () => KnowledgeSearchDialog.show(
                  ctx,
                  initialSubject: 'Operating Systems',
                ),
                child: const Text('Open Search'),
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      await tester.tap(find.text('Open Search'));
      await tester.pumpAndSettle();

      // Verify Dialog Title and Search Bar
      expect(find.text('Search Knowledge Base'), findsOneWidget);
      expect(find.byIcon(Icons.search_rounded), findsWidgets);
    });
  });
}
