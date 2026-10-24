import 'package:flutter/material.dart';
import '../models/competitive_exam_models.dart';
import '../services/competitive_exam_service.dart';
import 'pyq_practice_screen.dart';
import 'current_affairs_screen.dart';
import 'mains_answer_writing_screen.dart';

class CompetitiveExamDashboardScreen extends StatefulWidget {
  const CompetitiveExamDashboardScreen({super.key});

  @override
  State<CompetitiveExamDashboardScreen> createState() =>
      _CompetitiveExamDashboardScreenState();
}

class _CompetitiveExamDashboardScreenState
    extends State<CompetitiveExamDashboardScreen> {
  final CompetitiveExamService _service = CompetitiveExamService();
  bool _isLoading = true;
  ReadinessReportModel? _report;
  CompetitiveExamProfileModel? _profile;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final profile = await _service.getCurrentProfile();
    final report = await _service.getReadinessReport(examId: profile.examId);
    if (mounted) {
      setState(() {
        _profile = profile;
        _report = report;
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Competitive Exam Intelligence'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
            tooltip: 'Refresh Telemetry',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadData,
              child: ListView(
                padding: const EdgeInsets.all(16.0),
                children: [
                  _buildExamTargetHero(theme),
                  const SizedBox(height: 16),
                  _buildReadinessIndexCard(theme),
                  const SizedBox(height: 16),
                  _buildTodayPriorityCard(theme),
                  const SizedBox(height: 20),
                  Text(
                    'Practice & Intelligence Hubs',
                    style: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildFeatureGrid(context),
                  const SizedBox(height: 20),
                  _buildDisclaimerBanner(theme),
                ],
              ),
            ),
    );
  }

  Widget _buildExamTargetHero(ThemeData theme) {
    final name = _profile?.examName ?? 'UPSC Civil Services Examination';
    final year = _profile?.targetYear ?? 2027;
    final days = _report?.daysRemaining ?? 120;
    final hours = _profile?.dailyTargetHours ?? 6.0;

    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          gradient: LinearGradient(
            colors: [
              theme.colorScheme.primaryContainer,
              theme.colorScheme.surface,
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    'TARGET $year',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: theme.colorScheme.onPrimary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const Spacer(),
                const Icon(Icons.alarm, size: 18),
                const SizedBox(width: 4),
                Text(
                  '$days Days Remaining',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              name,
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Stage: ${_profile?.currentStage.toUpperCase() ?? 'PRELIMS'} • Daily Target: ${hours.toStringAsFixed(1)} hrs',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReadinessIndexCard(ThemeData theme) {
    final radar = _report?.readinessRadar ?? {};
    final overall = _report?.overallPreparationPercentage ?? 50.0;

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                Icon(Icons.insights, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  'Readiness Radar',
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Text(
                  '${overall.toStringAsFixed(1)}%',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.primary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: overall / 100.0,
                minHeight: 8,
                backgroundColor: theme.colorScheme.surfaceContainerHighest,
                color: theme.colorScheme.primary,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildMetricChip('Concept', radar['concept_readiness'] ?? 60.0, theme),
                _buildMetricChip('Prelims', radar['prelims_readiness'] ?? 55.0, theme),
                _buildMetricChip('Mains', radar['mains_readiness'] ?? 50.0, theme),
                _buildMetricChip('Revision', radar['revision_readiness'] ?? 70.0, theme),
                _buildMetricChip('Mock', radar['mock_readiness'] ?? 52.0, theme),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricChip(String label, double val, ThemeData theme) {
    return Column(
      children: [
        Text(
          '${val.round()}%',
          style: theme.textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
            color: val >= 65
                ? Colors.green[700]
                : (val >= 45 ? Colors.orange[800] : Colors.red[700]),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _buildTodayPriorityCard(ThemeData theme) {
    final priority = _report?.todayPriority ?? {};
    final topic = priority['topic'] as String? ?? 'Fundamental Rights & Constitutional Remedies';
    final rationale = priority['why_rationale'] as String? ?? 'High historical PYQ weightage.';

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.flag_circle, color: Colors.amber, size: 24),
                const SizedBox(width: 8),
                Text(
                  "Today's Priority Learning Focus",
                  style: theme.textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              topic,
              style: theme.textTheme.bodyLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              rationale,
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start Prioritized Session'),
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (context) => const PYQPracticeScreen(),
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

  Widget _buildFeatureGrid(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.15,
      children: [
        _buildNavCard(
          context: context,
          icon: Icons.quiz_outlined,
          title: 'PYQ Practice',
          subtitle: 'Past Year Questions & Error Diagnostics',
          color: Colors.blue,
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PYQPracticeScreen()),
          ),
        ),
        _buildNavCard(
          context: context,
          icon: Icons.newspaper_outlined,
          title: 'Current Affairs',
          subtitle: 'Daily High-Yield & Static Linking',
          color: Colors.deepPurple,
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const CurrentAffairsScreen()),
          ),
        ),
        _buildNavCard(
          context: context,
          icon: Icons.edit_note_outlined,
          title: 'Mains Writing',
          subtitle: '8-Rubric AI Evaluation & Outlines',
          color: Colors.teal,
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const MainsAnswerWritingScreen()),
          ),
        ),
        _buildNavCard(
          context: context,
          icon: Icons.timer_outlined,
          title: 'CSAT Aptitude',
          subtitle: 'Timed Comprehension & Reasoning',
          color: Colors.indigo,
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => const PYQPracticeScreen(initialStage: 'prelims'),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildNavCard({
    required BuildContext context,
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    final theme = Theme.of(context);
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: color.withAlpha(30),
                child: Icon(icon, color: color, size: 20),
              ),
              const SizedBox(height: 8),
              Text(
                title,
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontSize: 10,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDisclaimerBanner(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withAlpha(120),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, size: 16, color: theme.colorScheme.onSurfaceVariant),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Educational AI Coach: Insights and evaluations are structured for study guidance and are independent of official exam commissions.',
              style: theme.textTheme.bodySmall?.copyWith(
                fontSize: 11,
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
