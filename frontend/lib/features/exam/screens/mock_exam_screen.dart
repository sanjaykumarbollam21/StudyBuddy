import 'dart:async';
import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/exam_model.dart';
import '../services/exam_api_service.dart';
import 'exam_result_screen.dart';

class MockExamScreen extends StatefulWidget {
  final String? configId;
  final String subject;
  final int totalQuestions;

  const MockExamScreen({
    super.key,
    this.configId,
    this.subject = 'Operating Systems',
    this.totalQuestions = 6,
  });

  @override
  State<MockExamScreen> createState() => _MockExamScreenState();
}

class _MockExamScreenState extends State<MockExamScreen> {
  final ExamApiService _apiService = ExamApiService();

  bool _isLoading = true;
  MockExamSessionModel? _session;
  int _currentIndex = 0;

  // Answers record: question_id -> String response
  final Map<String, String> _answers = {};
  // Review flags: set of question_ids
  final Set<String> _reviewFlags = {};

  // Countdown timer
  Timer? _countdownTimer;
  int _secondsRemaining = 2700; // default 45 mins

  final TextEditingController _shortAnswerController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _startOrLoadExam();
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _shortAnswerController.dispose();
    super.dispose();
  }

  Future<void> _startOrLoadExam() async {
    setState(() => _isLoading = true);
    final session = await _apiService.startMockExam(
      configId: widget.configId,
      subject: widget.subject,
      totalQuestions: widget.totalQuestions,
    );

    if (mounted) {
      setState(() {
        _session = session;
        _secondsRemaining = session.timeRemainingSeconds > 0 ? session.timeRemainingSeconds : 2700;
        _isLoading = false;
      });
      _startTimer();
      _syncShortAnswerController();
    }
  }

  void _startTimer() {
    _countdownTimer?.cancel();
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_secondsRemaining <= 1) {
        timer.cancel();
        setState(() => _secondsRemaining = 0);
        _autoSubmitOnTimeExpiry();
      } else {
        setState(() {
          _secondsRemaining -= 1;
        });
      }
    });
  }

  void _syncShortAnswerController() {
    if (_session == null || _session!.questions.isEmpty) return;
    final currentQ = _session!.questions[_currentIndex];
    if (currentQ.questionType != 'mcq' && currentQ.questionType != 'multiple_select') {
      _shortAnswerController.text = _answers[currentQ.id] ?? '';
    }
  }

  void _autoSubmitOnTimeExpiry() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('⏱️ Time expired! Automatically submitting your exam...'),
        backgroundColor: AppColors.rose,
        duration: Duration(seconds: 3),
      ),
    );
    _submitExam();
  }

  String _formatTime(int seconds) {
    final m = seconds ~/ 60;
    final s = seconds % 60;
    final mm = m.toString().padLeft(2, '0');
    final ss = s.toString().padLeft(2, '0');
    return '$mm:$ss';
  }

  void _selectOption(String option) {
    if (_session == null) return;
    final q = _session!.questions[_currentIndex];

    setState(() {
      if (q.questionType == 'multiple_select') {
        final currentSelection = _answers[q.id]?.split(',').map((e) => e.trim()).where((e) => e.isNotEmpty).toList() ?? [];
        if (currentSelection.contains(option)) {
          currentSelection.remove(option);
        } else {
          currentSelection.add(option);
        }
        if (currentSelection.isEmpty) {
          _answers.remove(q.id);
        } else {
          _answers[q.id] = currentSelection.join(', ');
        }
      } else {
        // Single selection
        _answers[q.id] = option;
      }
    });
  }

  void _clearResponse() {
    if (_session == null) return;
    final q = _session!.questions[_currentIndex];
    setState(() {
      _answers.remove(q.id);
      _shortAnswerController.clear();
    });
  }

  void _toggleMarkForReview() {
    if (_session == null) return;
    final q = _session!.questions[_currentIndex];
    setState(() {
      if (_reviewFlags.contains(q.id)) {
        _reviewFlags.remove(q.id);
      } else {
        _reviewFlags.add(q.id);
      }
    });
  }

  void _goToQuestion(int index) {
    if (_session == null || index < 0 || index >= _session!.questions.length) return;
    setState(() {
      _currentIndex = index;
    });
    _syncShortAnswerController();
  }

  Future<void> _showSubmitConfirmationDialog() async {
    if (_session == null) return;
    final total = _session!.questions.length;
    final answered = _answers.keys.length;
    final unanswered = total - answered;
    final marked = _reviewFlags.length;

    final shouldSubmit = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: const [
            Icon(Icons.assignment_turned_in_rounded, color: AppColors.primary),
            SizedBox(width: 10),
            Text('Submit Examination?'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Please review your attempt summary before final submission. Negative marking applies to incorrect answers.',
              style: TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(ctx).colorScheme.surfaceContainerHighest.withAlpha(50),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.lightBorder),
              ),
              child: Column(
                children: [
                  _SummaryRow(label: 'Total Questions', value: '$total', color: AppColors.primary),
                  const Divider(height: 16),
                  _SummaryRow(label: 'Answered', value: '$answered', color: AppColors.emerald),
                  const Divider(height: 16),
                  _SummaryRow(label: 'Unanswered', value: '$unanswered', color: unanswered > 0 ? AppColors.rose : AppColors.lightTextSecondary),
                  const Divider(height: 16),
                  _SummaryRow(label: 'Marked for Review', value: '$marked', color: AppColors.amber),
                ],
              ),
            ),
            if (unanswered > 0)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Row(
                  children: const [
                    Icon(Icons.info_outline_rounded, size: 16, color: AppColors.rose),
                    SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Unanswered questions incur 0 marks and 0 negative penalty.',
                        style: TextStyle(fontSize: 11, color: AppColors.rose),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Return to Exam'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('Submit & View Results'),
          ),
        ],
      ),
    );

    if (shouldSubmit == true) {
      _submitExam();
    }
  }

  Future<void> _submitExam() async {
    if (_session == null) return;
    _countdownTimer?.cancel();
    setState(() => _isLoading = true);

    final result = await _apiService.submitMockExam(
      _session!.id,
      answers: _answers,
      timeSpentSeconds: _session!.durationMinutes * 60 - _secondsRemaining,
    );

    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => ExamResultScreen(result: result),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading || _session == null) {
      return Scaffold(
        appBar: AppBar(title: Text(widget.subject)),
        body: const Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Generating blueprint-aligned mock exam...', style: TextStyle(color: AppColors.lightTextSecondary)),
            ],
          ),
        ),
      );
    }

    final questions = _session!.questions;
    final currentQ = questions[_currentIndex];
    final isMarked = _reviewFlags.contains(currentQ.id);
    final hasAnswer = _answers.containsKey(currentQ.id);

    final isUrgentTime = _secondsRemaining < 300; // under 5 minutes

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_session!.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text('${_session!.subject} • Negative Marking: 0.25x', style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary)),
          ],
        ),
        actions: [
          // Live Countdown Badge
          Container(
            margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: isUrgentTime ? AppColors.rose.withAlpha(25) : AppColors.primary.withAlpha(20),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: isUrgentTime ? AppColors.rose : AppColors.primary,
                width: 1.2,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  Icons.timer_outlined,
                  size: 16,
                  color: isUrgentTime ? AppColors.rose : AppColors.primary,
                ),
                const SizedBox(width: 6),
                Text(
                  _formatTime(_secondsRemaining),
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: isUrgentTime ? AppColors.rose : AppColors.primary,
                  ),
                ),
              ],
            ),
          ),
          // Submit Button in Header
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ElevatedButton(
              onPressed: _showSubmitConfirmationDialog,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
              child: const Text('Submit', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Question Navigation Palette Bar
            _buildNavigationPalette(questions),

            const Divider(height: 1),

            // Question Workspace
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Question Header Card
                    _buildQuestionHeaderCard(currentQ, isMarked),

                    const SizedBox(height: 18),

                    // Prompt Box
                    Text(
                      currentQ.prompt,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        height: 1.45,
                      ),
                    ),

                    const SizedBox(height: 20),

                    // Options / Input Workspace
                    _buildAnswerOptions(currentQ),

                    const SizedBox(height: 30),
                  ],
                ),
              ),
            ),

            // Bottom Action Bar
            _buildBottomActionBar(questions.length, isMarked, hasAnswer),
          ],
        ),
      ),
    );
  }

  Widget _buildNavigationPalette(List<MockExamQuestionModel> questions) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      color: Theme.of(context).cardTheme.color,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'QUESTION PALETTE (${_currentIndex + 1}/${questions.length})',
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.lightTextSecondary),
              ),
              Wrap(
                spacing: 12,
                children: [
                  _PaletteLegendItem(color: AppColors.emerald, label: 'Answered'),
                  _PaletteLegendItem(color: AppColors.amber, label: 'Flagged'),
                  _PaletteLegendItem(color: Colors.grey.shade400, label: 'Unanswered'),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: List.generate(questions.length, (idx) {
                final q = questions[idx];
                final isCurrent = idx == _currentIndex;
                final isFlagged = _reviewFlags.contains(q.id);
                final isAnswered = _answers.containsKey(q.id);

                Color bgColor;
                Color textColor;
                if (isFlagged) {
                  bgColor = AppColors.amber;
                  textColor = Colors.white;
                } else if (isAnswered) {
                  bgColor = AppColors.emerald;
                  textColor = Colors.white;
                } else {
                  bgColor = Colors.grey.shade200;
                  textColor = Colors.black87;
                }

                return GestureDetector(
                  onTap: () => _goToQuestion(idx),
                  child: Container(
                    width: 36,
                    height: 36,
                    margin: const EdgeInsets.only(right: 8),
                    decoration: BoxDecoration(
                      color: bgColor,
                      borderRadius: BorderRadius.circular(8),
                      border: isCurrent
                          ? Border.all(color: AppColors.primary, width: 2.5)
                          : null,
                      boxShadow: isCurrent
                          ? [
                              BoxShadow(
                                color: AppColors.primary.withAlpha(50),
                                blurRadius: 4,
                                offset: const Offset(0, 2),
                              )
                            ]
                          : null,
                    ),
                    child: Center(
                      child: Text(
                        '${idx + 1}',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: isCurrent ? FontWeight.bold : FontWeight.w600,
                          color: textColor,
                        ),
                      ),
                    ),
                  ),
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionHeaderCard(MockExamQuestionModel currentQ, bool isMarked) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 4,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.primary.withAlpha(20),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                currentQ.topic.toUpperCase(),
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.primary),
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.grey.withAlpha(25),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                currentQ.questionType.replaceAll('_', ' ').toUpperCase(),
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppColors.lightTextSecondary),
              ),
            ),
          ],
        ),
        Text(
          '+${currentQ.marks.toInt()} Marks  •  -${currentQ.negativeMarks} Neg',
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.lightTextSecondary),
        ),
      ],
    );
  }

  Widget _buildAnswerOptions(MockExamQuestionModel q) {
    if (q.questionType == 'mcq' || q.questionType == 'multiple_select') {
      final isMulti = q.questionType == 'multiple_select';
      final currentSelected = isMulti
          ? (_answers[q.id]?.split(',').map((e) => e.trim()).toList() ?? [])
          : [_answers[q.id] ?? ''];

      return Column(
        children: q.options.map((option) {
          final isSelected = currentSelected.contains(option);
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: InkWell(
              onTap: () => _selectOption(option),
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: isSelected
                      ? AppColors.primary.withAlpha(15)
                      : Theme.of(context).cardTheme.color,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected ? AppColors.primary : AppColors.lightBorder,
                    width: isSelected ? 2.0 : 1.0,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 24,
                      height: 24,
                      decoration: BoxDecoration(
                        shape: isMulti ? BoxShape.rectangle : BoxShape.circle,
                        borderRadius: isMulti ? BorderRadius.circular(4) : null,
                        color: isSelected ? AppColors.primary : Colors.transparent,
                        border: Border.all(
                          color: isSelected ? AppColors.primary : Colors.grey.shade400,
                          width: 1.5,
                        ),
                      ),
                      child: isSelected
                          ? const Icon(Icons.check, size: 16, color: Colors.white)
                          : null,
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        option,
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      );
    } else {
      // Short answer / Scenario input
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TextField(
            controller: _shortAnswerController,
            maxLines: 4,
            decoration: InputDecoration(
              hintText: 'Enter your answer or key architectural principles...',
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              filled: true,
              fillColor: Theme.of(context).cardTheme.color,
            ),
            onChanged: (val) {
              setState(() {
                if (val.trim().isEmpty) {
                  _answers.remove(q.id);
                } else {
                  _answers[q.id] = val.trim();
                }
              });
            },
          ),
          const SizedBox(height: 8),
          const Text(
            'Tip: Be specific with technical terminology and trade-offs.',
            style: TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
          ),
        ],
      );
    }
  }

  Widget _buildBottomActionBar(int totalQuestions, bool isMarked, bool hasAnswer) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        border: const Border(top: BorderSide(color: AppColors.lightBorder)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Clear & Mark for Review Buttons
          Wrap(
            spacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: _toggleMarkForReview,
                style: OutlinedButton.styleFrom(
                  foregroundColor: isMarked ? AppColors.amber : AppColors.lightTextSecondary,
                  side: BorderSide(color: isMarked ? AppColors.amber : AppColors.lightBorder),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                ),
                icon: Icon(isMarked ? Icons.flag_rounded : Icons.outlined_flag_rounded, size: 16),
                label: Text(isMarked ? 'Flagged' : 'Flag', style: const TextStyle(fontSize: 12)),
              ),
              if (hasAnswer)
                TextButton(
                  onPressed: _clearResponse,
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.rose,
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  ),
                  child: const Text('Clear', style: TextStyle(fontSize: 12)),
                ),
            ],
          ),

          // Previous / Next Buttons
          Row(
            children: [
              IconButton(
                onPressed: _currentIndex > 0 ? () => _goToQuestion(_currentIndex - 1) : null,
                icon: const Icon(Icons.arrow_back_rounded),
                tooltip: 'Previous question',
              ),
              const SizedBox(width: 6),
              if (_currentIndex < totalQuestions - 1)
                ElevatedButton.icon(
                  onPressed: () => _goToQuestion(_currentIndex + 1),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.primary,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  icon: const Icon(Icons.arrow_forward_rounded, size: 16),
                  label: const Text('Next Question', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                )
              else
                ElevatedButton(
                  onPressed: _showSubmitConfirmationDialog,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.emerald,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: const Text('Review & Submit', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PaletteLegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _PaletteLegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: const TextStyle(fontSize: 10, color: AppColors.lightTextSecondary)),
      ],
    );
  }
}

class _SummaryRow extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _SummaryRow({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 13, color: AppColors.lightTextSecondary)),
        Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }
}
