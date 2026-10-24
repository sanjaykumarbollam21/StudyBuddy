import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../practice/models/practice_model.dart';
import '../../practice/services/practice_api_service.dart';
import '../../practice/screens/interactive_quiz_screen.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';
import '../../exam/screens/mock_exam_screen.dart';

class PracticeTab extends StatefulWidget {
  const PracticeTab({super.key});

  @override
  State<PracticeTab> createState() => _PracticeTabState();
}

class _PracticeTabState extends State<PracticeTab> {
  final PracticeApiService _apiService = PracticeApiService();
  final TextEditingController _customTopicController = TextEditingController();

  bool _isLoading = true;
  String _selectedTopic = 'Deadlocks & Banker\'s Algorithm';
  List<PracticeHistoryItemModel> _history = [];
  List<WeakAreaItemModel> _weakAreas = [];

  final List<String> _quickTopics = [
    'Deadlocks & Banker\'s Algorithm',
    'Process Synchronization',
    'CPU Scheduling Algorithms',
    'Relational Model & Normalization',
    'ACID Transactions & 2PL',
    'Linear & Logistic Regression',
    'Binary Search Trees',
  ];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _customTopicController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final history = await _apiService.getPracticeHistory();
      final weak = await _apiService.getWeakAreas();
      if (mounted) {
        setState(() {
          _history = history;
          _weakAreas = weak;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  void _startQuiz({required String topic, String mode = 'practice', int count = 5}) {
    InteractiveQuizScreen.open(
      context,
      topic: topic,
      sessionMode: mode,
      count: count,
    ).then((_) {
      _loadData();
    });
  }

  void _launchTeacherRemediation(String topic) {
    InteractiveTeacherScreen.open(
      context,
      topic: topic,
    );
  }

  void _startMockExam({String subject = 'Operating Systems'}) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => MockExamScreen(subject: subject),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 860),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header
                Text('Practice & Mastery Engine', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 6),
                const Text(
                  'Evidence-based testing across MCQs, scenarios, and coding questions with instant misconception diagnosis.',
                  style: TextStyle(color: AppColors.lightTextSecondary),
                ),
                const SizedBox(height: 12),
                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.only(bottom: 8),
                    child: LinearProgressIndicator(),
                  ),
                const SizedBox(height: 8),

                // Exam Readiness Hero Banner
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [AppColors.primaryDark, AppColors.primary],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: Colors.white.withAlpha(35),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(Icons.assignment_turned_in_rounded, color: Colors.white, size: 28),
                      ),
                      const SizedBox(width: 16),
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
                                  'EXAM READINESS: 68%',
                                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.amber),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.white24,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text('BLUEPRINT MODE', style: TextStyle(fontSize: 9, color: Colors.white)),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            const Text(
                              'Operating Systems Semester Exam',
                              style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 2),
                            const Text(
                              'Weighted blueprint across Processes, CPU, Sync, Deadlocks & Memory.',
                              style: TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      ElevatedButton(
                        onPressed: () => _startMockExam(subject: 'Operating Systems'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.white,
                          foregroundColor: AppColors.primaryDark,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: const Text('Start Mock Exam', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),


                // Topic Selector Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _quickTopics.map((topic) {
                      final isSelected = topic == _selectedTopic;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(topic),
                          selected: isSelected,
                          onSelected: (_) => setState(() => _selectedTopic = topic),
                          selectedColor: AppColors.primary.withAlpha(30),
                          labelStyle: TextStyle(
                            color: isSelected ? AppColors.primary : null,
                            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 20),

                // Practice Options (Quick Quiz vs Full Exam)
                Row(
                  children: [
                    Expanded(
                      child: _PracticeOptionCard(
                        title: 'Adaptive Concept Quiz',
                        description: '5 targeted questions with instant misconception feedback.',
                        icon: Icons.bolt_rounded,
                        color: AppColors.amber,
                        buttonText: 'Start Quick Quiz',
                        onTap: () => _startQuiz(topic: _selectedTopic, mode: 'practice', count: 5),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _PracticeOptionCard(
                        title: 'Deep Scenario & Mock Exam',
                        description: '10 comprehensive questions covering application & edge cases.',
                        icon: Icons.timer_rounded,
                        color: AppColors.rose,
                        buttonText: 'Start Mock Exam',
                        onTap: () => _startMockExam(subject: _selectedTopic),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 28),

                // Diagnosed Weak Areas & Misconceptions Section
                _buildWeakAreasSection(),
                const SizedBox(height: 28),

                // Recent Practice History
                _buildHistorySection(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildWeakAreasSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.psychology_rounded, color: AppColors.rose, size: 22),
            const SizedBox(width: 8),
            const Text('Diagnosed Weak Areas & Misconceptions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ],
        ),
        const SizedBox(height: 4),
        const Text(
          'Evidence gathered from incorrect answers and common distractor patterns.',
          style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
        ),
        const SizedBox(height: 14),

        if (_weakAreas.isEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.emerald.withAlpha(15),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.emerald.withAlpha(50)),
            ),
            child: Row(
              children: const [
                Icon(Icons.check_circle_rounded, color: AppColors.emerald),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'No persistent misconceptions detected! Great job across all practiced topics.',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
                  ),
                ),
              ],
            ),
          )
        else
          ..._weakAreas.map((weak) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(weak.topic, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                            Chip(
                              label: Text('Mastery: ${weak.masteryPercentage.toInt()}%'),
                              backgroundColor: AppColors.rose.withAlpha(20),
                              labelStyle: const TextStyle(color: AppColors.rose, fontSize: 11, fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.error_outline_rounded, size: 16, color: AppColors.rose),
                            const SizedBox(width: 6),
                            Expanded(
                              child: Text(
                                weak.primaryMisconception,
                                style: const TextStyle(fontSize: 13, height: 1.3),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          alignment: WrapAlignment.spaceBetween,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Text(
                              'Practiced ${weak.timesPracticed} times',
                              style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                            ),
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                ElevatedButton.icon(
                                  onPressed: () => _launchTeacherRemediation(weak.topic),
                                  icon: const Icon(Icons.school_rounded, size: 14),
                                  label: const Text('Re-teach with AI Teacher', style: TextStyle(fontSize: 12)),
                                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
                                ),
                                const SizedBox(width: 8),
                                OutlinedButton(
                                  onPressed: () => _startQuiz(topic: weak.topic, mode: 'practice', count: 3),
                                  child: const Text('Practice Again', style: TextStyle(fontSize: 12)),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              )),
      ],
    );
  }

  Widget _buildHistorySection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Recent Quiz Performance', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 14),

        if (_history.isEmpty)
          const Text('No quiz sessions recorded yet. Start your first quiz above!', style: TextStyle(color: AppColors.lightTextSecondary))
        else
          ..._history.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Card(
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: item.scorePercentage >= 70
                        ? AppColors.emerald.withAlpha(30)
                        : AppColors.rose.withAlpha(30),
                    child: Icon(
                      item.scorePercentage >= 70 ? Icons.check_circle_rounded : Icons.warning_rounded,
                      color: item.scorePercentage >= 70 ? AppColors.emerald : AppColors.rose,
                    ),
                  ),
                  title: Text(item.title, style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Text('${item.totalQuestions} questions • ${item.sessionMode.toUpperCase()}'),
                  trailing: Text(
                    '${item.scorePercentage.toInt()}%',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: item.scorePercentage >= 70 ? AppColors.emerald : AppColors.rose,
                    ),
                  ),
                  onTap: () => _startQuiz(topic: item.topic ?? item.title),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _PracticeOptionCard extends StatelessWidget {
  final String title;
  final String description;
  final IconData icon;
  final Color color;
  final String buttonText;
  final VoidCallback onTap;

  const _PracticeOptionCard({
    required this.title,
    required this.description,
    required this.icon,
    required this.color,
    required this.buttonText,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: color.withAlpha(25),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(height: 14),
            Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(description, style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary)),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onTap,
              style: ElevatedButton.styleFrom(
                backgroundColor: color,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              ),
              child: Text(buttonText),
            ),
          ],
        ),
      ),
    );
  }
}
