import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/features/voice/models/voice_model.dart';
import 'package:frontend/features/voice/services/voice_api_service.dart';
import 'package:frontend/features/voice/screens/voice_teacher_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Phase 8 Voice & Multimodal Teacher Data Models', () {
    test('MultimodalAnalysisModel serialization & parsing', () {
      final analysis = MultimodalAnalysisModel(
        imageType: 'diagram',
        detectedTopic: 'Deadlock Resource Allocation Graph',
        title: 'Resource Allocation Graph with Cycle',
        visualElements: ['Process P1 holding R1', 'Process P2 holding R2', 'Cycle P1->R2->P2->R1'],
        extractedText: 'P1 -> R2 -> P2 -> R1',
        conceptualExplanation: 'This graph contains a closed directed cycle representing a deadlock.',
        spokenScript: 'Notice the loop between P1 and P2. Neither can proceed.',
        checkQuestion: 'What condition does this cycle satisfy?',
        suggestedVoicePrompts: ['Explain circular wait', 'How to prevent this', 'Give me a hint'],
        ragCitations: [{'document_name': 'OS_Silberschatz.pdf', 'page_number': 42}],
      );

      final json = analysis.toJson();
      expect(json['image_type'], equals('diagram'));
      expect(json['detected_topic'], equals('Deadlock Resource Allocation Graph'));
      expect(json['visual_elements'].length, equals(3));

      final parsed = MultimodalAnalysisModel.fromJson(json);
      expect(parsed.imageType, equals('diagram'));
      expect(parsed.title, equals('Resource Allocation Graph with Cycle'));
      expect(parsed.checkQuestion, contains('What condition'));
      expect(parsed.ragCitations.first['page_number'], equals(42));
    });

    test('VoiceTurnModel parses and creates with multimodal payload', () {
      final turn = VoiceTurnModel(
        sessionId: 'sess-voice-999',
        intent: 'image_explanation',
        teacherReplyText: '### Diagram Breakdown\n\nCycle detected in graph.',
        spokenText: 'Here is what the diagram shows: a cyclic wait condition.',
        pedagogicalState: 'CHECK_UNDERSTANDING',
        conceptTitle: 'Resource Allocation Graph',
        suggestedQuickActions: ['Explain simpler', 'Quiz me'],
        citations: [{'doc': 'Notes.pdf', 'page': 12}],
      );

      final json = turn.toJson();
      expect(json['session_id'], equals('sess-voice-999'));
      expect(json['intent'], equals('image_explanation'));

      final parsed = VoiceTurnModel.fromJson(json);
      expect(parsed.sessionId, equals('sess-voice-999'));
      expect(parsed.teacherReplyText, contains('Diagram Breakdown'));
      expect(parsed.spokenText, contains('cyclic wait condition'));
      expect(parsed.suggestedQuickActions.length, equals(2));
    });
  });

  group('Phase 8 VoiceApiService Offline-First Fallbacks', () {
    final apiService = VoiceApiService();

    test('returns multimodal analysis for diagram requests', () async {
      final turn = await apiService.sendVoiceTurn(
        transcript: 'Can you explain this diagram to me?',
        currentTopic: 'Deadlocks',
        imageData: 'sample_diagram_data',
      );

      expect(turn.intent, equals('image_explanation'));
      expect(turn.multimodalAnalysis, isNotNull);
      expect(turn.multimodalAnalysis!.imageType, equals('diagram'));
      expect(turn.teacherReplyText, contains('Resource Allocation Graph'));
      expect(turn.spokenText.length, greaterThan(20));
      expect(turn.suggestedQuickActions.isNotEmpty, isTrue);
    });

    test('returns page-aware teaching for page 42 requests', () async {
      final turn = await apiService.sendVoiceTurn(
        transcript: 'Explain page 42 to me',
        currentTopic: 'Deadlocks',
        pageNumber: 42,
      );

      expect(turn.intent, equals('page_explanation'));
      expect(turn.teacherReplyText, contains('Page 42'));
      expect(turn.spokenText, contains('page 42'));
      expect(turn.conceptTitle, contains('Page 42'));
    });

    test('returns Socratic hint when student requests help', () async {
      final turn = await apiService.sendVoiceTurn(
        transcript: 'Give me a hint please',
        currentTopic: 'Deadlocks',
      );

      expect(turn.intent, equals('hint'));
      expect(turn.teacherReplyText, contains('Socratic Hint'));
      expect(turn.pedagogicalState, equals('REMEDIATE'));
    });

    test('returns simplified analogy when student expresses confusion', () async {
      final turn = await apiService.sendVoiceTurn(
        transcript: 'I do not understand this, make it easier',
        currentTopic: 'Deadlocks',
      );

      expect(turn.intent, equals('simplify'));
      expect(turn.teacherReplyText, contains('Real-Life Analogy'));
      expect(turn.spokenText, contains('forks'));
    });

    test('initiates quiz when student asks to be tested', () async {
      final turn = await apiService.sendVoiceTurn(
        transcript: 'Quiz me on this concept',
        currentTopic: 'Deadlocks',
      );

      expect(turn.intent, equals('quiz_me'));
      expect(turn.teacherReplyText, contains('Knowledge Check'));
      expect(turn.pedagogicalState, equals('CHECK_UNDERSTANDING'));
    });
  });

  group('Phase 8 VoiceTeacherScreen Widget Tests', () {
    testWidgets('renders voice teacher HUD with visualizer orb and dialogue', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: VoiceTeacherScreen(
            topic: 'Deadlocks & Resource Ordering',
            subject: 'Operating Systems',
          ),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));

      // 1. Verify AppBar and Topic
      expect(find.textContaining('Voice Teacher: Deadlocks'), findsOneWidget);
      expect(find.textContaining('Speech • Multimodal Visuals'), findsOneWidget);

      // 2. Verify Initial Teacher Greeting
      expect(find.textContaining('Study Buddy Voice Teacher'), findsOneWidget);
      expect(find.textContaining('I am your AI Teacher sitting right beside you'), findsOneWidget);

      // 3. Verify Initial Speaking HUD state & interrupt button
      expect(find.text('TEACHER SPEAKING (TAP TO INTERRUPT)'), findsOneWidget);

      // 4. Verify Spoken / Visual controls
      expect(find.byIcon(Icons.mic_none), findsOneWidget);
      expect(find.byIcon(Icons.add_photo_alternate_outlined), findsOneWidget);

      // 5. Allow greeting speech timer to finish -> transitions to ready
      await tester.pump(const Duration(seconds: 8));
      expect(find.text('VOICE TEACHER READY'), findsOneWidget);
    });

    testWidgets('quick prompt chips trigger conversational interaction', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: VoiceTeacherScreen(
            topic: 'Deadlocks',
            subject: 'Operating Systems',
          ),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));

      // Verify quick action chip exists
      final quizChip = find.text('Quiz me on this');
      expect(quizChip, findsOneWidget);

      // Tap "Quiz me on this" chip
      await tester.tap(quizChip);
      await tester.pump(const Duration(milliseconds: 200));

      // Now student message should show in feed
      expect(find.text('Quiz me on this'), findsWidgets);

      // Advance clock for simulated teacher response
      await tester.pump(const Duration(milliseconds: 800));

      // Verify Teacher responded with Knowledge Check
      expect(find.textContaining('Knowledge Check'), findsOneWidget);

      // Let speech timer finish
      await tester.pump(const Duration(seconds: 8));
    });

    testWidgets('multimodal attachment adds image and updates teacher explanation', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: VoiceTeacherScreen(
            topic: 'Deadlocks',
            subject: 'Operating Systems',
          ),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));

      // Tap multimodal camera/image icon
      final attachButton = find.byIcon(Icons.add_photo_alternate_outlined);
      expect(attachButton, findsOneWidget);
      await tester.tap(attachButton);
      await tester.pump(const Duration(milliseconds: 200));

      // Verify that media tray shows attached diagram
      expect(find.textContaining('Attached for Multimodal Analysis'), findsOneWidget);

      // Student taps a prompt while diagram is attached
      final explainChip = find.text('Explain Deadlocks to me');
      await tester.tap(explainChip);
      await tester.pump(const Duration(milliseconds: 200));

      // Advance clock for simulated multimodal processing
      await tester.pump(const Duration(milliseconds: 900));

      // Verify that diagram analysis appeared in dialogue
      expect(find.textContaining('Resource Allocation Graph'), findsOneWidget);
      expect(find.textContaining('Visual Elements Detected'), findsOneWidget);

      // Let speech timer finish
      await tester.pump(const Duration(seconds: 8));
    });

    testWidgets('teacher speech can be interrupted by student', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: VoiceTeacherScreen(
            topic: 'Deadlocks',
            subject: 'Operating Systems',
          ),
        ),
      );

      await tester.pump(const Duration(milliseconds: 300));

      // Greeting is speaking: verify speaking state
      expect(find.text('TEACHER SPEAKING (TAP TO INTERRUPT)'), findsOneWidget);

      // Tap the interrupt button in HUD
      final interruptButton = find.text('Interrupt');
      expect(interruptButton, findsOneWidget);
      await tester.tap(interruptButton);
      await tester.pump(const Duration(milliseconds: 200));

      // State switches to PAUSED
      expect(find.text('PAUSED'), findsOneWidget);

      // Pump out delay so all timers finish
      await tester.pump(const Duration(milliseconds: 600));
      expect(find.text('VOICE TEACHER READY'), findsOneWidget);
    });
  });
}
