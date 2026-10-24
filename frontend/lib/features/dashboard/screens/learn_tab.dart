import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../roadmap/models/roadmap_model.dart';
import '../../roadmap/services/roadmap_api_service.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';

class LearnTab extends StatefulWidget {
  const LearnTab({super.key});

  @override
  State<LearnTab> createState() => _LearnTabState();
}

class _LearnTabState extends State<LearnTab> {
  final TextEditingController _topicController = TextEditingController();
  final RoadmapApiService _apiService = RoadmapApiService();

  bool _isLoading = true;
  String _selectedSubject = 'Operating Systems';
  RoadmapModel? _currentRoadmap;
  NextRecommendationModel? _nextRecommendation;

  final List<String> _quickSubjects = [
    'Operating Systems',
    'Database Management Systems',
    'Machine Learning',
    'Python & Data Structures',
  ];

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  @override
  void dispose() {
    _topicController.dispose();
    super.dispose();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    try {
      final roadmap = await _apiService.generateRoadmap(subject: _selectedSubject);
      final nextRec = await _apiService.getNextRecommendation(roadmapId: roadmap.id);

      if (mounted) {
        setState(() {
          _currentRoadmap = roadmap;
          _nextRecommendation = nextRec;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }


  Future<void> _switchSubject(String subject) async {
    setState(() {
      _selectedSubject = subject;
      _isLoading = true;
    });

    final roadmap = await _apiService.generateRoadmap(subject: subject);
    final nextRec = await _apiService.getNextRecommendation(roadmapId: roadmap.id);

    if (mounted) {
      setState(() {
        _currentRoadmap = roadmap;
        _nextRecommendation = nextRec;
        _isLoading = false;
      });
    }
  }

  void _onGenerateCustom() {
    final query = _topicController.text.trim();
    if (query.isEmpty) return;
    _switchSubject(query);
    _topicController.clear();
  }

  void _showWhyLearningDialog(String topicTitle) async {
    showDialog(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => FutureBuilder<WhyLearningModel>(
        future: _apiService.getWhyLearning(
          topic: topicTitle,
          roadmapId: _currentRoadmap?.id,
          goal: _currentRoadmap?.goal,
        ),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const AlertDialog(
              content: SizedBox(
                height: 100,
                child: Center(child: CircularProgressIndicator()),
              ),
            );
          }

          final why = snapshot.data;
          if (why == null) {
            return const AlertDialog(
              content: Text('Unable to load learning rationale.'),
            );
          }

          return AlertDialog(
            title: Row(
              children: [
                const Icon(Icons.psychology_alt_rounded, color: AppColors.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Why Learn This?',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                  ),
                ),
              ],
            ),
            content: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    why.topicTitle,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary),
                  ),
                  const SizedBox(height: 12),

                  // Prerequisite link card
                  if (why.prerequisites.isNotEmpty) ...[
                    _buildRationaleCard(
                      icon: Icons.link_rounded,
                      title: 'Prerequisite Foundation',
                      subtitle: why.prerequisiteConnection,
                      color: AppColors.sky,
                    ),
                    const SizedBox(height: 10),
                  ],

                  // Core value card
                  _buildRationaleCard(
                    icon: Icons.auto_awesome_rounded,
                    title: 'Core Domain Value',
                    subtitle: why.coreValue,
                    color: AppColors.emerald,
                  ),
                  const SizedBox(height: 10),

                  // What it unlocks
                  if (why.unlockedNext.isNotEmpty) ...[
                    _buildRationaleCard(
                      icon: Icons.lock_open_rounded,
                      title: 'What It Unlocks',
                      subtitle: why.futureUnlocks,
                      color: AppColors.purple,
                    ),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Got It'),
              ),
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.of(ctx).pop();
                  _startLesson(topicTitle);
                },
                icon: const Icon(Icons.school_rounded, size: 16),
                label: const Text('Start Lesson'),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showLockedDialog(RoadmapTopicModel topic) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Row(
          children: const [
            Icon(Icons.lock_clock_rounded, color: AppColors.amber),
            SizedBox(width: 8),
            Text('Prerequisites Required'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Before starting "${topic.customTitle}", you should master its required foundational prerequisites:',
              style: const TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 12),
            ...topic.prerequisites.map(
              (p) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    const Icon(Icons.arrow_right_rounded, color: AppColors.primary),
                    const SizedBox(width: 4),
                    Expanded(
                      child: Text(
                        p,
                        style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.primary),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Mastering prerequisites first ensures you build strong intuition without getting stuck!',
              style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Understood'),
          ),
          if (topic.prerequisites.isNotEmpty)
            ElevatedButton(
              onPressed: () {
                Navigator.of(ctx).pop();
                _startLesson(topic.prerequisites.first);
              },
              child: Text('Study ${topic.prerequisites.first}'),
            ),
        ],
      ),
    );
  }

  Widget _buildRationaleCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withAlpha(60)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: color)),
                const SizedBox(height: 2),
                Text(subtitle, style: const TextStyle(fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _startLesson(String topicTitle) {
    InteractiveTeacherScreen.open(
      context,
      topic: topicTitle,
      subject: _selectedSubject,
    ).then((_) {
      // Refresh roadmap upon returning from lesson
      _loadInitialData();
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadInitialData,
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
                Text('Intelligent Curriculum & Roadmaps', style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 6),
                const Text(
                  'Knowledge-graph powered learning paths. Master concepts in strict prerequisite order with your personal AI teacher.',
                  style: TextStyle(color: AppColors.lightTextSecondary),
                ),
                const SizedBox(height: 20),

                // Track Quick-Selection Chips
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: _quickSubjects.map((sub) {
                      final isSelected = sub == _selectedSubject;
                      return Padding(
                        padding: const EdgeInsets.only(right: 8),
                        child: ChoiceChip(
                          label: Text(sub),
                          selected: isSelected,
                          onSelected: (_) => _switchSubject(sub),
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

                // Search & Custom Subject Input
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Theme.of(context).cardTheme.color,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: Theme.of(context).brightness == Brightness.dark
                          ? AppColors.darkBorder
                          : AppColors.lightBorder,
                    ),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _topicController,
                          decoration: InputDecoration(
                            hintText: 'Learn anything: e.g. Quantum Computing, Docker, Rust...',
                            prefixIcon: const Icon(Icons.auto_stories_rounded),
                            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                          ),
                          onSubmitted: (_) => _onGenerateCustom(),
                        ),
                      ),
                      const SizedBox(width: 12),
                      ElevatedButton.icon(
                        onPressed: _onGenerateCustom,
                        icon: const Icon(Icons.route_rounded, size: 18),
                        label: const Text('Generate Path'),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 40),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else ...[
                  // Hero "What Should I Learn Next?" Card
                  if (_nextRecommendation != null) _buildNextRecommendationHero(),
                  const SizedBox(height: 24),

                  // Roadmap Overview Header
                  _buildRoadmapOverviewHeader(),
                  const SizedBox(height: 16),

                  // Milestone Steps List (DAG Order)
                  _buildMilestoneList(),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildNextRecommendationHero() {
    final next = _nextRecommendation!;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.primaryDark.withAlpha(230),
            AppColors.primary,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
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
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(40),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.stars_rounded, color: Colors.amber, size: 16),
                    SizedBox(width: 6),
                    Text(
                      'RECOMMENDED NEXT STEP',
                      style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
              const Spacer(),
              Chip(
                label: Text('${next.estimatedMinutes} mins • ${next.difficulty}'),
                backgroundColor: Colors.white.withAlpha(30),
                labelStyle: const TextStyle(color: Colors.white, fontSize: 11),
                padding: EdgeInsets.zero,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            next.topicTitle,
            style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 6),
          Text(
            next.description,
            style: TextStyle(color: Colors.white.withAlpha(220), fontSize: 13),
          ),
          const SizedBox(height: 14),

          // Why Recommended Badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.black.withAlpha(40),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.info_outline_rounded, color: Colors.white70, size: 16),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    next.whyRecommended,
                    style: const TextStyle(color: Colors.white, fontSize: 12, height: 1.3),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          Row(
            children: [
              OutlinedButton.icon(
                onPressed: () => _showWhyLearningDialog(next.topicTitle),
                icon: const Icon(Icons.help_outline_rounded, size: 16, color: Colors.white),
                label: const Text('Why learn this?', style: TextStyle(color: Colors.white)),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Colors.white60),
                ),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: () => _startLesson(next.topicTitle),
                icon: const Icon(Icons.school_rounded, size: 18),
                label: const Text('Start Socratic Lesson'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: AppColors.primaryDark,
                  elevation: 2,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRoadmapOverviewHeader() {
    final roadmap = _currentRoadmap;
    if (roadmap == null) return const SizedBox.shrink();

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                roadmap.title,
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              if (roadmap.goal != null)
                Text(
                  roadmap.goal!,
                  style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                ),
            ],
          ),
        ),
        Chip(
          label: Text(
            '${roadmap.completedSteps} / ${roadmap.totalSteps} Mastered (${roadmap.progressPercentage.toInt()}%)',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
          ),
          backgroundColor: AppColors.primary.withAlpha(20),
        ),
      ],
    );
  }

  Widget _buildMilestoneList() {
    final roadmap = _currentRoadmap;
    if (roadmap == null || roadmap.topics.isEmpty) {
      return const Center(child: Text('No topics available.'));
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: roadmap.topics.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final topic = roadmap.topics[index];
        return _buildTopicCard(topic, index);
      },
    );
  }

  Widget _buildTopicCard(RoadmapTopicModel topic, int index) {
    Color statusColor;
    IconData statusIcon;
    String statusLabel;

    switch (topic.status) {
      case 'mastered':
        statusColor = AppColors.emerald;
        statusIcon = Icons.check_circle_rounded;
        statusLabel = 'Mastered';
        break;
      case 'in_progress':
        statusColor = AppColors.primary;
        statusIcon = Icons.play_circle_fill_rounded;
        statusLabel = 'In Progress';
        break;
      case 'unlocked':
        statusColor = AppColors.sky;
        statusIcon = Icons.lock_open_rounded;
        statusLabel = 'Ready to Learn';
        break;
      default:
        statusColor = AppColors.lightTextSecondary;
        statusIcon = Icons.lock_rounded;
        statusLabel = 'Locked';
    }

    final isLocked = topic.isLocked;

    return Card(
      elevation: topic.isInProgress ? 3 : 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: BorderSide(
          color: topic.isInProgress
              ? AppColors.primary
              : Theme.of(context).brightness == Brightness.dark
                  ? AppColors.darkBorder
                  : AppColors.lightBorder,
          width: topic.isInProgress ? 1.5 : 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Step Badge Icon
                CircleAvatar(
                  backgroundColor: statusColor.withAlpha(30),
                  child: Icon(statusIcon, color: statusColor, size: 22),
                ),
                const SizedBox(width: 14),

                // Title & Subtitle
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${topic.orderIndex}. ${topic.customTitle}',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: isLocked ? AppColors.lightTextSecondary : null,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: statusColor.withAlpha(20),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              statusLabel,
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: statusColor),
                            ),
                          ),
                        ],
                      ),
                      if (topic.description != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          topic.description!,
                          style: TextStyle(
                            fontSize: 13,
                            color: isLocked ? AppColors.lightTextSecondary.withAlpha(160) : AppColors.lightTextSecondary,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),

            // Prerequisites Pill if any
            if (topic.prerequisites.isNotEmpty) ...[
              const SizedBox(height: 10),
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: isLocked ? AppColors.amber.withAlpha(20) : Colors.grey.withAlpha(20),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          isLocked ? Icons.lock_clock_rounded : Icons.check_circle_outline_rounded,
                          size: 12,
                          color: isLocked ? AppColors.amber : AppColors.emerald,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Requires: ${topic.prerequisites.join(", ")}',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: isLocked ? AppColors.amber : AppColors.lightTextSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ],

            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 10),

            // Bottom Actions & Meta
            Row(
              children: [
                Text(
                  '${topic.estimatedMinutes} mins • ${topic.difficulty}',
                  style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                ),
                const Spacer(),
                // Why learn this button
                TextButton.icon(
                  onPressed: () => _showWhyLearningDialog(topic.customTitle),
                  icon: const Icon(Icons.info_outline_rounded, size: 14),
                  label: const Text('Why learn this?', style: TextStyle(fontSize: 12)),
                ),
                const SizedBox(width: 8),

                // Action button
                if (isLocked)
                  OutlinedButton.icon(
                    onPressed: () => _showLockedDialog(topic),
                    icon: const Icon(Icons.lock_rounded, size: 14),
                    label: const Text('Locked', style: TextStyle(fontSize: 12)),
                  )
                else
                  ElevatedButton.icon(
                    onPressed: () => _startLesson(topic.customTitle),
                    icon: Icon(
                      topic.isMastered ? Icons.replay_rounded : Icons.school_rounded,
                      size: 14,
                    ),
                    label: Text(
                      topic.isMastered
                          ? 'Review'
                          : topic.isInProgress
                              ? 'Continue'
                              : 'Start Lesson',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
