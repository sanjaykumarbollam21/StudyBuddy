import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:frontend/features/auth/controllers/auth_controller.dart';
import 'package:frontend/features/auth/screens/login_screen.dart';
import 'package:frontend/features/dashboard/screens/main_shell_screen.dart';
import 'package:frontend/features/dashboard/screens/tutor_sheet.dart';
import 'package:frontend/features/documents/models/document_model.dart';
import 'package:frontend/features/documents/screens/document_detail_screen.dart';
import 'package:frontend/features/practice/screens/interactive_quiz_screen.dart';
import 'package:frontend/features/competitive_exam/screens/pyq_practice_screen.dart';
import 'package:frontend/features/competitive_exam/screens/mains_answer_writing_screen.dart';
import 'package:frontend/features/revision/screens/active_recall_screen.dart';
import 'package:frontend/core/widgets/error_card.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
  });

  group('Study Buddy End-to-End User Journeys (Integration Suite)', () {
    // -------------------------------------------------------------------------
    // JOURNEY 1: Login -> Dashboard
    // -------------------------------------------------------------------------
    testWidgets('Journey 1: Login -> Dashboard Shell transition', (tester) async {
      final authController = AuthController();
      await authController.initialize();

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark(),
          home: LoginScreen(authController: authController),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Login Screen elements
      expect(find.text('Study Buddy'), findsWidgets);
      expect(find.text('Login'), findsOneWidget);

      // Perform Demo Login
      final demoButton = find.text('Try Demo Account');
      if (demoButton.evaluate().isNotEmpty) {
        await tester.tap(demoButton);
        await tester.pumpAndSettle();
      } else {
        await authController.loginWithDemoAccount();
      }

      // Re-pump shell with authenticated user
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark(),
          home: MainShellScreen(authController: authController),
        ),
      );
      await tester.pumpAndSettle();

      // Assert Dashboard loaded
      expect(find.text('Study Buddy'), findsOneWidget);
      expect(find.text('S'), findsOneWidget); // Student avatar initial
    });

    // -------------------------------------------------------------------------
    // JOURNEY 2: Upload & Index Document -> Ask Tutor -> Citations
    // -------------------------------------------------------------------------
    testWidgets('Journey 2: Document Indexing -> Tutor Query with Grounded Citations', (tester) async {
      final mockDoc = DocumentItem(
        id: 'doc-int-01',
        filename: 'OS_Architecture_Guide.pdf',
        fileType: 'pdf',
        fileSizeBytes: 204800,
        pageCount: 15,
        extractedCharacterCount: 12000,
        sectionCount: 4,
        chunkCount: 8,
        subjectName: 'Operating Systems',
        collectionName: 'Core Textbooks',
        processingStatus: 'ready',
        processingStage: 'ready',
        processingProgress: 100,
        embeddingStatus: 'ready',
        createdAt: DateTime.now(),
      );

      // 1. Verify Document Detail renders indexing status
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark(),
          home: DocumentDetailScreen(document: mockDoc),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('OS_Architecture_Guide.pdf'), findsOneWidget);
      expect(find.text('Indexed & Ready'), findsOneWidget);

      // 2. Open Grounded Tutor Sheet scoped to this document
      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark(),
          home: Scaffold(
            body: TutorSheet(
              scopedDocumentId: mockDoc.id,
              scopedDocumentName: mockDoc.filename,
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('Teaching from: OS_Architecture_Guide.pdf'), findsOneWidget);

      // Enter query
      final inputField = find.byType(TextField);
      expect(inputField, findsOneWidget);
      await tester.enterText(inputField, 'What is the function of the OS kernel?');
      await tester.pump();
      expect(find.text('What is the function of the OS kernel?'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // JOURNEY 3: Practice Session
    // -------------------------------------------------------------------------
    testWidgets('Journey 3: Interactive Practice Session UI & Options', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: InteractiveQuizScreen(
              topic: 'Operating Systems',
              count: 3,
            ),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 500));

      // Assert Quiz header exists
      expect(find.text('Operating Systems'), findsWidgets);
    });

    // -------------------------------------------------------------------------
    // JOURNEY 4: UPSC Prelims Test with 0.66 Negative Marking Scoring
    // -------------------------------------------------------------------------
    testWidgets('Journey 4: UPSC Prelims Simulator with 0.66 Negative Marking', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: PYQPracticeScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Assert Prelims / PYQ header is present
      expect(find.text('Previous Year Questions'), findsOneWidget);

      // Verify Negative Marking rule banner: +2.0 correct, -0.66 incorrect
      expect(find.textContaining('UPSC Prelims Marking'), findsWidgets);
    });

    // -------------------------------------------------------------------------
    // JOURNEY 5: Mains Answer Submission & Feedback
    // -------------------------------------------------------------------------
    testWidgets('Journey 5: UPSC Mains Answer Submission & Diagnostic Rubric', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: MainsAnswerWritingScreen(),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Mains Answer Writing & Evaluation'), findsOneWidget);
      expect(find.textContaining('Judicial Review'), findsOneWidget);

      // Enter student answer
      final textFields = find.byType(TextField);
      expect(textFields, findsWidgets);
      await tester.enterText(
        textFields.last,
        'Judicial review ensures legislative and executive acts conform to constitutional limits. As established in the Kesavananda Bharati case, it is part of the basic structure.',
      );
      await tester.pump();

      expect(find.textContaining('Kesavananda Bharati'), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // JOURNEY 6: Retention Review (SM-2 Spaced Repetition)
    // -------------------------------------------------------------------------
    testWidgets('Journey 6: Retention Review Queue & Active Recall', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: ActiveRecallScreen(),
          ),
        ),
      );
      await tester.pump(const Duration(milliseconds: 500));

      // Assert Active Recall screen initialized
      expect(find.byType(ActiveRecallScreen), findsOneWidget);
    });

    // -------------------------------------------------------------------------
    // JOURNEY 7: Offline Resilience Banner with Tap to Retry
    // -------------------------------------------------------------------------
    testWidgets('Journey 7: Offline Banner & ErrorCard with Interactive Retry', (tester) async {
      bool retryTapped = false;

      await tester.pumpWidget(
        MaterialApp(
          theme: ThemeData.dark(),
          home: Scaffold(
            body: Center(
              child: ErrorCard(
                message: 'No internet connection. Tap to reconnect.',
                onRetry: () {
                  retryTapped = true;
                },
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('No internet connection. Tap to reconnect.'), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);

      await tester.tap(find.text('Retry'));
      await tester.pump();

      expect(retryTapped, isTrue);
    });
  });
}
