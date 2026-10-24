import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/revision_model.dart';
import '../services/revision_api_service.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';

class ActiveRecallScreen extends StatefulWidget {
  const ActiveRecallScreen({super.key});

  static Future<void> open(BuildContext context) {
    return Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const ActiveRecallScreen()),
    );
  }

  @override
  State<ActiveRecallScreen> createState() => _ActiveRecallScreenState();
}

class _ActiveRecallScreenState extends State<ActiveRecallScreen> {
  final RevisionApiService _apiService = RevisionApiService();
  final TextEditingController _studentRecallController = TextEditingController();

  bool _isLoading = true;
  bool _isSubmitting = false;
  List<RevisionItemModel> _queue = [];
  int _currentIndex = 0;
  bool _isAnswerRevealed = false;
  SubmitReviewResponseModel? _lastResult;

  final List<Map<String, dynamic>> _completedReviews = [];

  @override
  void initState() {
    super.initState();
    _loadQueue();
  }

  @override
  void dispose() {
    _studentRecallController.dispose();
    super.dispose();
  }

  Future<void> _loadQueue() async {
    setState(() => _isLoading = true);
    final items = await _apiService.getDueReviews(limit: 10);
    if (mounted) {
      setState(() {
        _queue = items;
        _isLoading = false;
        _resetCard();
      });
    }
  }

  void _resetCard() {
    _isAnswerRevealed = false;
    _studentRecallController.clear();
    _lastResult = null;
  }

  Future<void> _rateRecall(int rating) async {
    if (_queue.isEmpty || _currentIndex >= _queue.length) return;

    final currentItem = _queue[_currentIndex];
    setState(() => _isSubmitting = true);

    final res = await _apiService.submitReview(
      itemId: currentItem.id,
      qualityRating: rating,
      studentRecall: _studentRecallController.text.trim(),
    );

    if (mounted) {
      setState(() {
        _isSubmitting = false;
        _lastResult = res;
        _completedReviews.add({
          'topic': currentItem.topicTitle,
          'rating': rating,
          'nextInterval': res.newIntervalDays,
          'isPassed': res.isPassed,
        });
      });
    }
  }

  void _advanceToNext() {
    if (_currentIndex + 1 < _queue.length) {
      setState(() {
        _currentIndex += 1;
        _resetCard();
      });
    } else {
      setState(() {
        _currentIndex += 1; // triggers completion view
      });
    }
  }

  void _launchTeacher(String topic) {
    InteractiveTeacherScreen.open(
      context,
      topic: topic,
    );
  }

  @override
  Widget build(BuildContext context) {
    final isFinished = !_isLoading && (_queue.isEmpty || _currentIndex >= _queue.length);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Active Recall & Retrieval'),
        actions: [
          if (!_isLoading && _queue.isNotEmpty && _currentIndex < _queue.length)
            Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Center(
                child: Text(
                  '${_currentIndex + 1} of ${_queue.length}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                ),
              ),
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : isFinished
              ? _buildCompletedView()
              : _buildRecallBody(),
    );
  }

  Widget _buildRecallBody() {
    final item = _queue[_currentIndex];

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 780),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Overdue Alert Badge
              if (item.daysOverdue > 0)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: AppColors.amber.withAlpha(20),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.amber.withAlpha(60)),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.history_rounded, size: 16, color: AppColors.amber),
                      const SizedBox(width: 8),
                      Text(
                        'Overdue by ${item.daysOverdue.toInt()} day${item.daysOverdue.toInt() == 1 ? "" : "s"} • Memory decay accelerating',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.amber),
                      ),
                    ],
                  ),
                ),

              // Active Challenge Card
              Card(
                elevation: 3,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              item.topicTitle,
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                          ),
                          Chip(
                            label: Text('Interval: ${item.intervalDays}d'),
                            backgroundColor: AppColors.primary.withAlpha(20),
                            labelStyle: const TextStyle(fontSize: 11, color: AppColors.primary),
                          ),
                        ],
                      ),
                      if (item.conceptSummary != null) ...[
                        const SizedBox(height: 6),
                        Text(
                          item.conceptSummary!,
                          style: const TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
                        ),
                      ],
                      const SizedBox(height: 16),
                      const Divider(),
                      const SizedBox(height: 12),

                      // Retrieval Challenge
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Theme.of(context).cardTheme.color,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.lightBorder),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: const [
                                Icon(Icons.psychology_alt_rounded, color: AppColors.primary, size: 18),
                                SizedBox(width: 6),
                                Text(
                                  'ACTIVE RETRIEVAL PROBE',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.primary),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              item.retrievalPrompt,
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, height: 1.4),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Optional Student Recall Scratchpad
                      if (!_isAnswerRevealed) ...[
                        TextField(
                          controller: _studentRecallController,
                          maxLines: 3,
                          decoration: InputDecoration(
                            hintText: 'Type your mental recall here before checking answer (optional)...',
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                            contentPadding: const EdgeInsets.all(12),
                          ),
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          width: double.infinity,
                          height: 46,
                          child: ElevatedButton.icon(
                            onPressed: () => setState(() => _isAnswerRevealed = true),
                            icon: const Icon(Icons.visibility_rounded, size: 18),
                            label: const Text('Reveal Key Concepts & Verify Recall', style: TextStyle(fontWeight: FontWeight.bold)),
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
              ),

              // Canonical Answer & SM-2 Self-Rating Bar
              if (_isAnswerRevealed) ...[
                const SizedBox(height: 20),
                _buildRevealedAnswerCard(item),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRevealedAnswerCard(RevisionItemModel item) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.emerald.withAlpha(15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.emerald.withAlpha(60), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.check_circle_rounded, color: AppColors.emerald, size: 20),
              SizedBox(width: 8),
              Text(
                'Key Canonical Concepts',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.emerald),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            item.retrievalAnswer,
            style: const TextStyle(fontSize: 14, height: 1.4),
          ),
          const SizedBox(height: 20),
          const Divider(),
          const SizedBox(height: 12),

          if (_lastResult == null) ...[
            const Text(
              'How accurately did you retrieve this concept?',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            const SizedBox(height: 12),

            // Quality Scale 0 to 5
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                _buildRatingButton(0, 'Blackout (0)', AppColors.rose),
                _buildRatingButton(2, 'Failed Recall (2)', AppColors.rose),
                _buildRatingButton(3, 'Hard Recall (3)', AppColors.amber),
                _buildRatingButton(4, 'Good Recall (4)', AppColors.sky),
                _buildRatingButton(5, 'Perfect Recall (5)', AppColors.emerald),
              ],
            ),
          ] else ...[
            // Result & Next Navigation
            _buildPostRatingStatus(),
          ],
        ],
      ),
    );
  }

  Widget _buildRatingButton(int rating, String label, Color color) {
    return OutlinedButton(
      onPressed: _isSubmitting ? null : () => _rateRecall(rating),
      style: OutlinedButton.styleFrom(
        foregroundColor: color,
        side: BorderSide(color: color),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      ),
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
    );
  }

  Widget _buildPostRatingStatus() {
    final res = _lastResult!;
    final isPassed = res.isPassed;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: isPassed ? AppColors.emerald.withAlpha(20) : AppColors.rose.withAlpha(20),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Row(
            children: [
              Icon(
                isPassed ? Icons.schedule_rounded : Icons.warning_rounded,
                color: isPassed ? AppColors.emerald : AppColors.rose,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isPassed
                          ? 'Next review scheduled in ${res.newIntervalDays} day${res.newIntervalDays == 1 ? "" : "s"}'
                          : 'Retention lapsed: Scheduled for immediate review tomorrow',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: isPassed ? AppColors.emerald : AppColors.rose,
                      ),
                    ),
                    Text(
                      'Hardened Topic Mastery: ${res.updatedMasteryPercentage.toInt()}%',
                      style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        if (!isPassed && res.remediationAdvice != null) ...[
          const SizedBox(height: 12),
          ElevatedButton.icon(
            onPressed: () => _launchTeacher(_queue[_currentIndex].topicTitle),
            icon: const Icon(Icons.school_rounded, size: 16),
            label: const Text('Re-teach with Socratic AI Teacher', style: TextStyle(fontSize: 12)),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.rose),
          ),
        ],
        const SizedBox(height: 16),
        Align(
          alignment: Alignment.centerRight,
          child: ElevatedButton(
            onPressed: _advanceToNext,
            child: const Text('Next Active Recall Card'),
          ),
        ),
      ],
    );
  }

  Widget _buildCompletedView() {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 600),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const CircleAvatar(
                radius: 40,
                backgroundColor: AppColors.emeraldLight,
                child: Icon(Icons.verified_rounded, color: AppColors.emerald, size: 48),
              ),
              const SizedBox(height: 20),
              Text('Spaced Repetition Completed!', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 8),
              const Text(
                'Great job strengthening your long-term memory retrieval pathways today.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.lightTextSecondary),
              ),
              const SizedBox(height: 24),

              // Summary list
              if (_completedReviews.isNotEmpty) ...[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Session Retention Summary', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
                        const SizedBox(height: 12),
                        ..._completedReviews.map(
                          (r) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              children: [
                                Icon(
                                  r['isPassed'] as bool ? Icons.check_circle : Icons.refresh,
                                  color: r['isPassed'] as bool ? AppColors.emerald : AppColors.rose,
                                  size: 16,
                                ),
                                const SizedBox(width: 8),
                                Expanded(child: Text(r['topic'] as String, style: const TextStyle(fontSize: 13))),
                                Text(
                                  'Next: ${r['nextInterval']}d',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
              ],

              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Back to Today\'s Learning Hub'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
