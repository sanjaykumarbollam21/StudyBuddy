import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:frontend/core/storage/offline_storage_service.dart';
import 'package:frontend/features/auth/controllers/auth_controller.dart';
import 'package:frontend/features/revision/services/revision_api_service.dart';
import 'package:frontend/features/practice/services/practice_api_service.dart';
import 'package:frontend/features/roadmap/services/roadmap_api_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('Multi-User Data Isolation & Fresh User Onboarding Tests', () {
    test('New user sign up creates clean isolated profile with zero pre-existing data', () async {
      final auth = AuthController();
      final storage = OfflineStorageService();
      final revisionApi = RevisionApiService();
      final practiceApi = PracticeApiService();
      final roadmapApi = RoadmapApiService();

      // 1. Sign up new user Alice
      final successAlice = await auth.signup(
        email: 'alice.aspirant@upsc.gov.in',
        password: 'password123',
        fullName: 'Alice Aspirant',
      );
      expect(successAlice, isTrue);
      expect(auth.currentUser, isNotNull);
      expect(auth.currentUser!.email, equals('alice.aspirant@upsc.gov.in'));
      expect(storage.activeUserId, equals(auth.currentUser!.id));

      // 2. Verify all data is completely fresh and isolated for Alice
      final aliceMastery = await storage.loadAllMastery();
      expect(aliceMastery.isEmpty, isTrue);

      final aliceReviews = await revisionApi.getDueReviews();
      expect(aliceReviews.isEmpty, isTrue, reason: 'New user must have 0 due reviews');

      final aliceAgenda = await revisionApi.getDailyAgenda();
      expect(aliceAgenda.dueForReviewCount, equals(0));
      expect(aliceAgenda.reviewStreakDays, equals(0));

      final aliceHistory = await practiceApi.getPracticeHistory();
      expect(aliceHistory.isEmpty, isTrue);

      final aliceWeakAreas = await practiceApi.getWeakAreas();
      expect(aliceWeakAreas.isEmpty, isTrue);

      final aliceRoadmap = await roadmapApi.generateRoadmap(subject: 'Operating Systems');
      expect(aliceRoadmap.completedSteps, equals(0));
      expect(aliceRoadmap.progressPercentage, equals(0.0));
      expect(aliceRoadmap.topics.first.masteryScore, equals(0.0));

      final aliceDocs = await storage.loadUserDocuments();
      expect(aliceDocs.isEmpty, isTrue);

      // 3. Alice studies and earns progress
      await storage.saveMastery('Indian Polity', 88.0);
      await storage.saveRevisionItems([
        {'id': 'polity-rev-1', 'topic_title': 'Preamble', 'interval_days': 3}
      ]);
      await storage.saveUserDocuments([
        {'id': 'doc-alice-1', 'filename': 'Laxmikanth_Notes.pdf', 'file_type': 'pdf'}
      ]);

      expect((await storage.loadAllMastery())['indian polity'], equals(88.0));
      expect((await storage.loadUserDocuments()).length, equals(1));

      // 4. Alice logs out
      await auth.logout();
      expect(auth.isAuthenticated, isFalse);

      // 5. Brand new user Bob signs up
      final successBob = await auth.signup(
        email: 'bob.engineer@gate.ac.in',
        password: 'password456',
        fullName: 'Bob Engineer',
      );
      expect(successBob, isTrue);
      expect(storage.activeUserId, equals(auth.currentUser!.id));
      expect(auth.currentUser!.id, isNot(equals('alice.aspirant@upsc.gov.in')));

      // 6. Verify Bob has ZERO data and does NOT inherit Alice's progress
      final bobMastery = await storage.loadAllMastery();
      expect(bobMastery.isEmpty, isTrue, reason: 'Bob must not see Alice mastery');

      final bobReviews = await revisionApi.getDueReviews();
      expect(bobReviews.isEmpty, isTrue, reason: 'Bob must have 0 due reviews');

      final bobDocs = await storage.loadUserDocuments();
      expect(bobDocs.isEmpty, isTrue, reason: 'Bob must not see Alice documents');

      // 7. Bob logs out and Alice logs back in
      await auth.logout();
      final loginAlice = await auth.login(
        email: 'alice.aspirant@upsc.gov.in',
        password: 'password123',
      );
      expect(loginAlice, isTrue);
      expect(storage.activeUserId, equals(auth.currentUser!.id));

      // 8. Verify Alice's data was preserved in her isolated partition
      final aliceRestoredMastery = await storage.loadAllMastery();
      expect(aliceRestoredMastery['indian polity'], equals(88.0));
      final aliceRestoredDocs = await storage.loadUserDocuments();
      expect(aliceRestoredDocs.length, equals(1));
      expect(aliceRestoredDocs[0]['filename'], equals('Laxmikanth_Notes.pdf'));

      // 9. Alice resets her learning data cleanly
      await auth.resetCurrentUserData();
      final aliceClearedMastery = await storage.loadAllMastery();
      expect(aliceClearedMastery.isEmpty, isTrue);
      final aliceClearedDocs = await storage.loadUserDocuments();
      expect(aliceClearedDocs.isEmpty, isTrue);
    });
  });
}
