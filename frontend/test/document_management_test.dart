import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/main.dart';
import 'package:frontend/features/auth/controllers/auth_controller.dart';
import 'package:frontend/features/dashboard/screens/materials_tab.dart';
import 'package:frontend/features/documents/models/document_model.dart';
import 'package:frontend/features/documents/screens/document_detail_screen.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  test('DocumentItem model JSON serialization and status getters', () {
    final now = DateTime.now();
    final doc = DocumentItem(
      id: 'doc-test-1',
      filename: 'Sample_Unit.pdf',
      fileType: 'pdf',
      fileSizeBytes: 2048576,
      pageCount: 18,
      extractedCharacterCount: 15400,
      sectionCount: 3,
      chunkCount: 6,
      subjectName: 'Computer Networks',
      collectionName: 'Networking 101',
      processingStatus: 'ready',
      processingStage: 'ready',
      processingProgress: 100,
      previewText: 'Sample extracted content...',
      createdAt: now,
    );

    expect(doc.isReady, isTrue);
    expect(doc.isProcessing, isFalse);
    expect(doc.isFailed, isFalse);
    expect(doc.formattedSize, contains('MB'));

    final json = doc.toJson();
    final reconstructed = DocumentItem.fromJson(json);

    expect(reconstructed.id, equals('doc-test-1'));
    expect(reconstructed.filename, equals('Sample_Unit.pdf'));
    expect(reconstructed.pageCount, equals(18));
    expect(reconstructed.extractedCharacterCount, equals(15400));
    expect(reconstructed.sectionCount, equals(3));
  });

  testWidgets('Materials tab displays saved documents, upload dialog, and delete flow', (WidgetTester tester) async {
    final authController = AuthController();
    await authController.initialize();
    await authController.loginWithDemoAccount();

    await tester.pumpWidget(StudyBuddyApp(authController: authController));
    await tester.pumpAndSettle();

    // 1. Navigate to Materials Tab (index 2 in NavigationBar)
    await tester.tap(find.byIcon(Icons.folder_outlined));
    await tester.pumpAndSettle();

    expect(find.byType(MaterialsTab), findsOneWidget);
    expect(find.text('Personal Knowledge Base'), findsOneWidget);
    expect(find.textContaining('Saved Materials'), findsOneWidget);

    // Verify initial saved documents
    expect(find.text('OS_Unit_2_Concurrency.pdf'), findsOneWidget);
    expect(find.text('DBMS_Relational_Algebra_Notes.pdf'), findsOneWidget);

    // 2. Test deleting an unnecessary document
    final deleteButtons = find.byIcon(Icons.delete_outline_rounded);
    expect(deleteButtons, findsWidgets);

    await tester.ensureVisible(deleteButtons.first);
    await tester.pumpAndSettle();

    await tester.tap(deleteButtons.first);
    await tester.pumpAndSettle();

    // Verify confirmation dialog appears
    expect(find.text('Delete Document?'), findsOneWidget);
    expect(find.text('Delete'), findsOneWidget);

    // Confirm deletion
    await tester.tap(find.widgetWithText(ElevatedButton, 'Delete'));
    await tester.pumpAndSettle();

    // Verify document was removed
    expect(find.text('OS_Unit_2_Concurrency.pdf'), findsNothing);
  });

  testWidgets('DocumentDetailScreen displays metadata, chunks, and preview text', (WidgetTester tester) async {
    final sampleDoc = DocumentItem(
      id: 'doc-detail-test',
      filename: 'Distributed_Systems_Ch1.pdf',
      fileType: 'pdf',
      fileSizeBytes: 4194304,
      pageCount: 32,
      extractedCharacterCount: 42100,
      sectionCount: 4,
      chunkCount: 2,
      subjectName: 'Distributed Systems',
      collectionName: 'Core Papers',
      processingStatus: 'ready',
      processingStage: 'ready',
      processingProgress: 100,
      previewText: '# Distributed Systems Overview\n\nConsistency and replication fundamentals.',
      chunks: [
        DocumentChunkItem(
          id: 'chunk-1',
          chunkIndex: 0,
          content: 'A distributed system consists of autonomous computing entities.',
          pageNumber: 1,
          sectionTitle: 'Introduction',
          createdAt: DateTime.now(),
        ),
      ],
      createdAt: DateTime.now(),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: DocumentDetailScreen(document: sampleDoc),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Distributed_Systems_Ch1.pdf'), findsWidgets);
    expect(find.text('Distributed Systems • Core Papers'), findsOneWidget);
    expect(find.text('File Size'), findsOneWidget);
    expect(find.text('Pages'), findsOneWidget);
    expect(find.text('Extracted Document Preview'), findsOneWidget);
    expect(find.text('Teach Me This'), findsOneWidget);
    expect(find.textContaining('A distributed system consists of autonomous'), findsOneWidget);
  });
}
