import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';
import '../../revision/screens/active_recall_screen.dart';
import '../../practice/screens/interactive_quiz_screen.dart';
import '../../exam/screens/mock_exam_screen.dart';
import '../models/planner_model.dart';
import '../services/planner_api_service.dart';

class StudyPlannerScreen extends StatefulWidget {
  final String subject;

  const StudyPlannerScreen({
    super.key,
    this.subject = 'Operating Systems',
  });

  static Future<void> open(BuildContext context, {String subject = 'Operating Systems'}) {
    return Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => StudyPlannerScreen(subject: subject),
      ),
    );
  }

  @override
  State<StudyPlannerScreen> createState() => _StudyPlannerScreenState();
}

class _StudyPlannerScreenState extends State<StudyPlannerScreen> {
  final PlannerApiService _apiService = PlannerApiService();

  bool _isLoading = true;
  StudyPlanModel? _plan;
  AgentChatResponseModel? _latestAgentResponse;
  bool _isAgentThinking = false;

  final TextEditingController _customAgentInputController = TextEditingController();

  final List<String> _quickPrompts = [
    'What should I study now?',
    'I have 30 minutes',
    'I missed yesterday',
    'Focus on weak areas',
    'Start 20-question practice',
    'Test exam readiness',
    'Move exam date',
  ];

  @override
  void initState() {
    super.initState();
    _loadPlan();
  }

  @override
  void dispose() {
    _customAgentInputController.dispose();
    super.dispose();
  }

  Future<void> _loadPlan() async {
    setState(() => _isLoading = true);
    final plan = await _apiService.getActivePlan(subject: widget.subject);
    if (mounted) {
      setState(() {
        _plan = plan;
        _isLoading = false;
      });
      // Initial agent greeting
      _handleAgentMessage('What should I study now?');
    }
  }

  Future<void> _handleAgentMessage(String prompt) async {
    setState(() => _isAgentThinking = true);
    final res = await _apiService.sendAgentMessage(prompt, planId: _plan?.id);
    if (mounted) {
      setState(() {
        _latestAgentResponse = res;
        _isAgentThinking = false;
      });
    }
  }

  void _executeAgentAction(AgentActionPayloadModel action) {
    switch (action.actionType) {
      case 'socratic_lesson':
        InteractiveTeacherScreen.open(
          context,
          topic: action.topic,
          subject: action.subject,
        ).then((_) => _loadPlan());
        break;

      case 'active_recall':
        ActiveRecallScreen.open(context).then((_) => _loadPlan());
        break;

      case 'practice_quiz':
        InteractiveQuizScreen.open(
          context,
          topic: action.topic,
          count: action.metadata['question_count'] as int? ?? 15,
        ).then((_) => _loadPlan());
        break;

      case 'mock_exam':
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => MockExamScreen(subject: action.subject),
          ),
        ).then((_) => _loadPlan());
        break;

      case 'replan_view':
      default:
        _showReplanModal();
        break;
    }
  }

  void _launchSessionItem(StudyPlanItemModel item) {
    switch (item.actionType) {
      case 'socratic_lesson':
        InteractiveTeacherScreen.open(
          context,
          topic: item.topic,
          subject: _plan?.subject,
        ).then((_) => _loadPlan());
        break;

      case 'active_recall':
        ActiveRecallScreen.open(context).then((_) => _loadPlan());
        break;

      case 'practice_quiz':
        InteractiveQuizScreen.open(
          context,
          topic: item.topic,
          count: item.actionPayload['question_count'] as int? ?? 20,
        ).then((_) => _loadPlan());
        break;

      case 'mock_exam':
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => MockExamScreen(subject: _plan?.subject ?? 'Operating Systems'),
          ),
        ).then((_) => _loadPlan());
        break;

      default:
        InteractiveTeacherScreen.open(context, topic: item.topic, subject: _plan?.subject)
            .then((_) => _loadPlan());
        break;
    }
  }

  void _showReplanModal() {
    int missedDays = 1;
    int? newDaysLeft;

    showModalBottomSheet(
      context: context,
      isScrollControlled: false,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModalState) => SingleChildScrollView(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 24,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('🔄 Dynamic Re-Plan Agent', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                ],
              ),
              const SizedBox(height: 6),
              const Text(
                'Tell Study Buddy what changed. The planner recalculates your trajectory without penalties.',
                style: TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
              ),
              const SizedBox(height: 18),
              const Text('Did you miss any study days?', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [1, 2, 3].map((d) {
                  final isSelected = missedDays == d;
                  return ChoiceChip(
                    label: Text('$d day${d > 1 ? 's' : ''} missed'),
                    selected: isSelected,
                    onSelected: (val) {
                      if (val) setModalState(() => missedDays = d);
                    },
                  );
                }).toList(),
              ),
              const SizedBox(height: 18),
              const Text('Or change target exam deadline:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [5, 7, 10, 14, 21].map((days) {
                  final isSelected = newDaysLeft == days;
                  return ChoiceChip(
                    label: Text('$days days left'),
                    selected: isSelected,
                    onSelected: (val) {
                      setModalState(() => newDaysLeft = val ? days : null);
                    },
                  );
                }).toList(),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () async {
                    Navigator.pop(ctx);
                    setState(() => _isLoading = true);
                    final updated = await _apiService.replan(
                      missedDays: missedDays,
                      newDaysUntilExam: newDaysLeft,
                      reason: 'Student recalculated timeline in modal',
                    );
                    setState(() {
                      _plan = updated;
                      _isLoading = false;
                    });
                    _handleAgentMessage('Recalculated study plan trajectory');
                  },
                  icon: const Icon(Icons.auto_awesome_rounded),
                  label: const Text('Recalculate & Optimize Timetable', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Intelligent Study Planner & AI Agent',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Text(
              '${widget.subject} • Proactive Autonomous Learning Coordinator',
              style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.sync_rounded),
            tooltip: 'Recalculate Plan',
            onPressed: _showReplanModal,
          ),
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
            onPressed: _loadPlan,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadPlan,
              child: SingleChildScrollView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 860),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // 1. Proactive Agent Header & Status Hub
                        _buildAgentStatusHub(isDark),
                        const SizedBox(height: 18),

                        // 2. AI Study Companion Chat & Prompt Strip
                        _buildAgentCompanionCard(isDark),
                        const SizedBox(height: 22),

                        // 3. Today's Action Plan (Session Blocks)
                        _buildTodayPlanSection(isDark),
                        const SizedBox(height: 26),

                        // 4. Long-Term Multi-Day Strategy Trajectory
                        _buildLongTermTrajectorySection(isDark),
                      ],
                    ),
                  ),
                ),
              ),
            ),
    );
  }

  Widget _buildAgentStatusHub(bool isDark) {
    final plan = _plan;
    final currentDay = plan?.currentDay ?? 1;
    final totalDays = plan?.totalDays ?? 12;
    final availableHours = plan?.totalAvailableHours ?? 24.0;
    final dailyHours = ((plan?.dailyStudyMinutes ?? 120) / 60.0).toStringAsFixed(1);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: isDark
              ? [const Color(0xFF1E1B4B), const Color(0xFF312E81)]
              : [AppColors.primary, AppColors.primaryDark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withAlpha(50),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(40),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.smart_toy_rounded, color: Colors.white, size: 14),
                    SizedBox(width: 6),
                    Text(
                      'AI STUDY PLANNER AGENT',
                      style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              OutlinedButton.icon(
                onPressed: _showReplanModal,
                style: OutlinedButton.styleFrom(
                  foregroundColor: Colors.white,
                  side: const BorderSide(color: Colors.white60),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  minimumSize: Size.zero,
                ),
                icon: const Icon(Icons.sync_rounded, size: 14),
                label: const Text('Replan Schedule', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            plan?.title ?? 'Operating Systems Exam Prep Plan',
            style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            'Target Exam in ${totalDays - currentDay + 1} days • $dailyHours hrs/day pacing • Dynamic adjustments active',
            style: const TextStyle(color: Colors.white70, fontSize: 12),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              _buildStatPill('DAY $currentDay OF $totalDays', Icons.calendar_today_rounded, AppColors.amber),
              const SizedBox(width: 10),
              _buildStatPill('${availableHours.toStringAsFixed(1)}h AVAILABLE', Icons.timer_rounded, AppColors.emerald),
              const SizedBox(width: 10),
              _buildStatPill('CONTINUOUS RE-PLAN', Icons.auto_awesome_rounded, AppColors.sky),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatPill(String text, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withAlpha(25),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 14),
          const SizedBox(width: 6),
          Text(
            text,
            style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildAgentCompanionCard(bool isDark) {
    final response = _latestAgentResponse;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: AppColors.primaryLight, width: 1.2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 16,
                  backgroundColor: AppColors.primary.withAlpha(30),
                  child: const Icon(Icons.psychology_rounded, color: AppColors.primary, size: 18),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Study Buddy Autonomous Agent',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                const Spacer(),
                if (_isAgentThinking)
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isDark ? AppColors.darkSurfaceAlt : AppColors.lightSurfaceAlt,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                response?.message ??
                    'I am your AI Study Agent. Ask me what to study next, tell me how much time you have, or let me know if you missed a session.',
                style: const TextStyle(fontSize: 13, height: 1.4),
              ),
            ),
            if (response != null && response.suggestedAction != null) ...[
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _executeAgentAction(response.suggestedAction!),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 10),
                  ),
                  icon: const Icon(Icons.play_arrow_rounded, size: 18),
                  label: Text(
                    'Execute Action: ${response.suggestedAction!.actionType.replaceAll('_', ' ').toUpperCase()} (${response.suggestedAction!.topic})',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 14),
            // Quick prompt chips
            const Text(
              'Quick Prompts:',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.lightTextSecondary),
            ),
            const SizedBox(height: 6),
            SizedBox(
              height: 38,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: _quickPrompts.length,
                itemBuilder: (ctx, idx) {
                  final prompt = _quickPrompts[idx];
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ActionChip(
                      label: Text(prompt, style: const TextStyle(fontSize: 11)),
                      onPressed: () => _handleAgentMessage(prompt),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTodayPlanSection(bool isDark) {
    final todayItems = _plan?.todayItems ?? [];
    final currentDay = _plan?.currentDay ?? 1;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                const Icon(Icons.today_rounded, size: 20, color: AppColors.primary),
                const SizedBox(width: 8),
                Text(
                  'Today\'s Priority Action Plan (Day $currentDay)',
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            Chip(
              label: Text('${todayItems.length} SESSIONS'),
              backgroundColor: AppColors.primary.withAlpha(20),
              labelStyle: const TextStyle(color: AppColors.primary, fontSize: 10, fontWeight: FontWeight.bold),
              padding: EdgeInsets.zero,
            ),
          ],
        ),
        const SizedBox(height: 4),
        const Text(
          'Targeted sessions ordered by prerequisite dependencies, weak-area gaps, and spaced retention.',
          style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
        ),
        const SizedBox(height: 12),
        if (todayItems.isEmpty)
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Theme.of(context).cardTheme.color,
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Center(
              child: Text('All tasks for today are completed! Great job.'),
            ),
          )
        else
          ...todayItems.map((item) => _buildSessionItemCard(item, isDark)),
      ],
    );
  }

  Widget _buildSessionItemCard(StudyPlanItemModel item, bool isDark) {
    Color badgeColor;
    IconData typeIcon;
    switch (item.sessionType) {
      case 'learn':
        badgeColor = AppColors.primary;
        typeIcon = Icons.school_rounded;
        break;
      case 'practice':
        badgeColor = AppColors.amber;
        typeIcon = Icons.quiz_rounded;
        break;
      case 'revision':
        badgeColor = AppColors.purple;
        typeIcon = Icons.psychology_alt_rounded;
        break;
      case 'mock_exam':
        badgeColor = AppColors.rose;
        typeIcon = Icons.assignment_rounded;
        break;
      default:
        badgeColor = AppColors.emerald;
        typeIcon = Icons.check_circle_rounded;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: 1,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: badgeColor.withAlpha(25),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(typeIcon, color: badgeColor, size: 22),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: badgeColor.withAlpha(20),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          item.sessionType.toUpperCase(),
                          style: TextStyle(color: badgeColor, fontSize: 10, fontWeight: FontWeight.bold),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        '${item.allocatedMinutes} mins',
                        style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                      ),
                      const Spacer(),
                      Chip(
                        label: Text('${(item.priorityWeight * 100).toInt()}% PRIORITY'),
                        backgroundColor: AppColors.rose.withAlpha(15),
                        labelStyle: const TextStyle(color: AppColors.rose, fontSize: 9, fontWeight: FontWeight.bold),
                        padding: EdgeInsets.zero,
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    item.topic,
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () => _launchSessionItem(item),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                      ),
                      icon: const Icon(Icons.arrow_forward_rounded, size: 16),
                      label: Text(
                        'Launch ${item.sessionType.toUpperCase()}',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLongTermTrajectorySection(bool isDark) {
    final strategy = _plan?.strategySummary ?? {};
    final phases = (strategy['phases'] as List<dynamic>?) ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: const [
            Icon(Icons.timeline_rounded, size: 20, color: AppColors.primary),
            SizedBox(width: 8),
            Text(
              'Dynamic Long-Term Trajectory',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
          ],
        ),
        const SizedBox(height: 4),
        const Text(
          'Automated four-phase roadmap balancing foundation building, retrieval, and full exam readiness.',
          style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
        ),
        const SizedBox(height: 14),
        if (phases.isEmpty)
          const Text('Standard 4-phase preparation active.')
        else
          ...phases.map((ph) {
            final phaseMap = ph as Map<String, dynamic>;
            return Card(
              margin: const EdgeInsets.only(bottom: 10),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: ListTile(
                leading: CircleAvatar(
                  backgroundColor: AppColors.primary.withAlpha(25),
                  child: Text(
                    '${phaseMap['phase_number']}',
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ),
                title: Text(
                  phaseMap['name'] as String? ?? 'Phase',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                ),
                subtitle: Text(
                  '${phaseMap['days']} • ${phaseMap['focus']}',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            );
          }),
      ],
    );
  }
}
