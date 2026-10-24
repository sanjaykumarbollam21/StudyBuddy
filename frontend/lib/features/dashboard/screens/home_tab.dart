import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/stat_badge.dart';
import '../../auth/controllers/auth_controller.dart';
import '../../revision/models/revision_model.dart';
import '../../revision/services/revision_api_service.dart';
import '../../revision/screens/active_recall_screen.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';
import '../../voice/screens/voice_teacher_screen.dart';
import '../../planner/screens/study_planner_screen.dart';
import '../../teaching/models/teaching_model.dart';
import '../../teaching/services/teaching_api_service.dart';
import 'tutor_sheet.dart';

class HomeTab extends StatefulWidget {
  final AuthController authController;
  final Function(int) onTabNavigate;
  final TeachingApiService? teachingApiService;

  const HomeTab({
    super.key,
    required this.authController,
    required this.onTabNavigate,
    this.teachingApiService,
  });

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  final RevisionApiService _revisionApi = RevisionApiService();
  late final TeachingApiService _teachingApi;

  DailyAgendaModel? _agenda;
  List<ActiveTeachingSessionModel> _activeSessions = [];

  @override
  void initState() {
    super.initState();
    _teachingApi = widget.teachingApiService ?? TeachingApiService();
    _loadAgenda();
  }

  Future<void> _loadAgenda() async {
    final agenda = await _revisionApi.getDailyAgenda();
    List<ActiveTeachingSessionModel> sessions = [];
    try {
      sessions = await _teachingApi.getActiveSessions();
    } catch (_) {}
    if (mounted) {
      setState(() {
        _agenda = agenda;
        _activeSessions = sessions;
      });
    }
  }

  String _getGreeting() {
    final hour = DateTime.now().hour;
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  void _resumeLesson(String topic) {
    InteractiveTeacherScreen.open(
      context,
      topic: topic,
    ).then((_) => _loadAgenda());
  }

  void _startActiveRecall() {
    ActiveRecallScreen.open(context).then((_) => _loadAgenda());
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.authController.currentUser;
    final studentName = user?.displayName ?? 'Student';
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final agenda = _agenda;

    return RefreshIndicator(
      onRefresh: _loadAgenda,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 800),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 1. Personalized Greeting & Streak Badge
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${_getGreeting()}, $studentName 👋',
                            style: Theme.of(context).textTheme.headlineMedium,
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'Your personal AI teacher is managing your learning today.',
                            style: TextStyle(
                              color: AppColors.lightTextSecondary,
                              fontSize: 14,
                            ),
                          ),
                        ],
                      ),
                    ),
                    StatBadge(
                      icon: Icons.local_fire_department_rounded,
                      label: '${agenda?.reviewStreakDays ?? 4} Day Streak',
                      color: AppColors.amber,
                      backgroundColor: AppColors.amberLight,
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // 2. Continue Learning Hero Card or Active Session Card
                if (_activeSessions.isNotEmpty) ...[
                  _buildContinueSessionCard(_activeSessions.first, isDark),
                ] else ...[
                  _buildContinueLearningHero(isDark, agenda),
                ],
                const SizedBox(height: 24),

                // 3. "Today's Learning" Hub (Spaced Repetition & Priority Matrix)
                _buildTodaysLearningSection(agenda),
                const SizedBox(height: 28),

                // 4. Quick Actions Grid
                Text(
                  'Quick Actions',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 14),
                _buildQuickActionsGrid(agenda),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildContinueSessionCard(ActiveTeachingSessionModel session, bool isDark) {
    return Container(
      key: const Key('continue_session_card'),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E293B) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primary.withValues(alpha: 0.3), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'CONTINUE WHERE YOU LEFT OFF',
                style: TextStyle(
                  color: AppColors.primary,
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
              Text(
                'Step ${session.currentStepIndex + 1} of ${session.totalSteps}',
                style: TextStyle(
                  color: isDark ? Colors.white70 : Colors.black54,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            session.topic,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          if (session.conceptTitle != null) ...[
            const SizedBox(height: 4),
            Text(
              session.conceptTitle!,
              style: TextStyle(
                color: isDark ? Colors.white60 : Colors.black45,
                fontSize: 14,
              ),
            ),
          ],
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${session.masteryScore.toInt()}% Mastery',
                style: const TextStyle(
                  color: AppColors.emerald,
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
              ElevatedButton.icon(
                key: const Key('resume_session_button'),
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => InteractiveTeacherScreen(
                        topic: session.topic,
                        sessionId: session.sessionId,
                        apiService: widget.teachingApiService,
                      ),
                    ),
                  ).then((_) => _loadAgenda());
                },
                icon: const Icon(Icons.play_arrow_rounded, size: 18),
                label: const Text('Resume'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildContinueLearningHero(bool isDark, DailyAgendaModel? agenda) {
    final topic = agenda?.continueLearning.topic ?? 'Deadlocks & Banker\'s Algorithm';
    final progress = agenda?.continueLearning.progressText ?? 'Step 3 of 5';
    final subject = agenda?.continueLearning.subject ?? 'Operating Systems';

    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isDark
              ? [const Color(0xFF1E1B4B), const Color(0xFF312E81)]
              : [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withAlpha(60),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(50),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.play_circle_fill_rounded, color: Colors.white, size: 14),
                    SizedBox(width: 6),
                    Text(
                      'CONTINUE LEARNING',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ],
                ),
              ),
              Text(
                progress,
                style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            topic,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Subject: $subject • Ready for next concept step',
            style: const TextStyle(color: Colors.white70, fontSize: 13),
          ),
          const SizedBox(height: 18),
          // Progress bar
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: const LinearProgressIndicator(
              value: 0.60,
              backgroundColor: Colors.white24,
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.emerald),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              ElevatedButton.icon(
                onPressed: () => _resumeLesson(topic),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: AppColors.primaryDark,
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: const Icon(Icons.arrow_forward_rounded, size: 18),
                label: const Text('Resume With AI Teacher', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
              OutlinedButton.icon(
                onPressed: () {
                  VoiceTeacherScreen.open(
                    context,
                    topic: topic,
                    subject: subject,
                  );
                },
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white70),
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: const Icon(Icons.mic_rounded, size: 18),
                label: const Text('Voice Mode', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
              TextButton(
                onPressed: () => widget.onTabNavigate(1), // Go to Learn tab
                style: TextButton.styleFrom(foregroundColor: Colors.white),
                child: const Text('View Full Roadmap'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildTodaysLearningSection(DailyAgendaModel? agenda) {
    final dueCount = agenda?.dueForReviewCount ?? 3;
    final weakConcept = agenda?.topWeakArea.concept ?? 'Circular Wait';
    final weakMastery = agenda?.topWeakArea.masteryPercentage ?? 42.0;
    final weakTopic = agenda?.topWeakArea.topic ?? 'Deadlocks';
    final recommended = agenda?.recommendedAction ?? '5-minute active retrieval on overdue concepts';
    final examPriority = agenda?.examPriority ?? 'CPU Scheduling Algorithms';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: const [
            Icon(Icons.calendar_today_rounded, size: 20, color: AppColors.primary),
            SizedBox(width: 8),
            Text(
              "Today's Learning Plan",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 4),
        const Text(
          'Intelligent retention queue: Overdue concepts, weak areas, and active retrieval targets.',
          style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
        ),
        const SizedBox(height: 14),

        // 2x2 Grid of Spaced Repetition Cards
        Row(
          children: [
            // Due for Review Card
            Expanded(
              child: Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: AppColors.primaryLight, width: 1.2),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withAlpha(25),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.psychology_rounded, color: AppColors.primary, size: 20),
                          ),
                          Chip(
                            label: Text('$dueCount DUE TODAY'),
                            backgroundColor: AppColors.primary.withAlpha(20),
                            labelStyle: const TextStyle(
                              color: AppColors.primary,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                            padding: EdgeInsets.zero,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Due for Review',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '$dueCount concepts scheduled for SM-2 active recall.',
                        style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton(
                          onPressed: _startActiveRecall,
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                          child: const Text('Start Active Recall', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 14),

            // Weak Area Alert Card
            Expanded(
              child: Card(
                elevation: 2,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                  side: const BorderSide(color: AppColors.rose, width: 1.2),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.rose.withAlpha(25),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.warning_amber_rounded, color: AppColors.rose, size: 20),
                          ),
                          Chip(
                            label: Text('${weakMastery.toInt()}% MASTERY'),
                            backgroundColor: AppColors.rose.withAlpha(20),
                            labelStyle: const TextStyle(
                              color: AppColors.rose,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                            padding: EdgeInsets.zero,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      const Text(
                        'Weak Area Alert',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '$weakConcept ($weakTopic)',
                        style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton(
                          onPressed: () => _resumeLesson(weakTopic),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppColors.rose,
                            side: const BorderSide(color: AppColors.rose),
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                          child: const Text('Fix Weak Concept', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),

        // Recommended Action & Exam Priority Row
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Theme.of(context).cardTheme.color,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: Theme.of(context).brightness == Brightness.dark
                  ? AppColors.darkBorder
                  : AppColors.lightBorder,
            ),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.amber.withAlpha(25),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.stars_rounded, color: AppColors.amber, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        const Text(
                          '🎯 RECOMMENDED TODAY',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.amber),
                        ),
                        Text(
                          '• 🔥 Exam Priority: $examPriority',
                          style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      recommended,
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
              ElevatedButton(
                onPressed: _startActiveRecall,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.amber,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                ),
                child: const Text('Start Now', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildQuickActionsGrid(DailyAgendaModel? agenda) {
    return GridView.count(
      crossAxisCount: MediaQuery.of(context).size.width > 600 ? 3 : 2,
      crossAxisSpacing: 14,
      mainAxisSpacing: 14,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      childAspectRatio: 2.1,
      children: [
        _QuickActionCard(
          title: 'AI Study Planner',
          subtitle: 'Proactive study agent',
          icon: Icons.auto_awesome_rounded,
          color: AppColors.primary,
          onTap: () {
            StudyPlannerScreen.open(
              context,
              subject: agenda?.continueLearning.subject ?? 'Operating Systems',
            );
          },
        ),
        _QuickActionCard(
          title: 'Voice Teacher',
          subtitle: 'Spoken & visual tutor',
          icon: Icons.mic_rounded,
          color: AppColors.purple,
          onTap: () {
            VoiceTeacherScreen.open(
              context,
              topic: agenda?.continueLearning.topic ?? 'Operating Systems - Deadlocks',
              subject: agenda?.continueLearning.subject ?? 'Operating Systems',
            );
          },
        ),
        _QuickActionCard(
          title: 'Active Recall',
          subtitle: 'Spaced repetition queue',
          icon: Icons.psychology_alt_rounded,
          color: AppColors.primary,
          onTap: _startActiveRecall,
        ),
        _QuickActionCard(
          title: 'Ask Study Buddy',
          subtitle: 'Socratic dialogue',
          icon: Icons.smart_toy_rounded,
          color: AppColors.primaryLight,
          onTap: () {
            TutorSheet.show(context);
          },
        ),
        _QuickActionCard(
          title: 'Curriculum Path',
          subtitle: 'Knowledge graph roadmap',
          icon: Icons.explore_rounded,
          color: AppColors.emerald,
          onTap: () => widget.onTabNavigate(1), // Learn tab
        ),
        _QuickActionCard(
          title: 'Practice & Quizzes',
          subtitle: 'Evidence-based tests',
          icon: Icons.quiz_rounded,
          color: AppColors.amber,
          onTap: () => widget.onTabNavigate(3), // Practice tab
        ),
        _QuickActionCard(
          title: 'Upload Material',
          subtitle: 'Upload PDFs & notes',
          icon: Icons.upload_file_rounded,
          color: AppColors.sky,
          onTap: () => widget.onTabNavigate(2), // Materials tab
        ),
        _QuickActionCard(
          title: 'Student Progress',
          subtitle: 'Mastery analytics',
          icon: Icons.insights_rounded,
          color: AppColors.rose,
          onTap: () => widget.onTabNavigate(4), // Progress tab
        ),
      ],
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: color.withAlpha(25),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Icon(icon, color: color, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      subtitle,
                      style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
