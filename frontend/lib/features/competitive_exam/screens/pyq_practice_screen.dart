import 'package:flutter/material.dart';
import '../models/competitive_exam_models.dart';
import '../services/competitive_exam_service.dart';

class PYQPracticeScreen extends StatefulWidget {
  final String initialStage;
  const PYQPracticeScreen({super.key, this.initialStage = 'prelims'});

  @override
  State<PYQPracticeScreen> createState() => _PYQPracticeScreenState();
}

class _PYQPracticeScreenState extends State<PYQPracticeScreen> {
  final CompetitiveExamService _service = CompetitiveExamService();
  bool _isLoading = true;
  List<PYQModel> _questions = [];
  int _currentIndex = 0;
  String? _selectedOption;
  PYQAttemptResultModel? _lastResult;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _loadQuestions();
  }

  Future<void> _loadQuestions() async {
    setState(() => _isLoading = true);
    final list = await _service.getPYQs(stage: widget.initialStage);
    if (mounted) {
      setState(() {
        _questions = list;
        _isLoading = false;
        _currentIndex = 0;
        _selectedOption = null;
        _lastResult = null;
      });
    }
  }

  Future<void> _submitCurrent() async {
    if (_selectedOption == null || _questions.isEmpty) return;
    setState(() => _isSubmitting = true);
    final q = _questions[_currentIndex];
    final res = await _service.submitPYQAttempt(
      questionId: q.id,
      selectedOption: _selectedOption!,
    );
    if (mounted) {
      setState(() {
        _lastResult = res;
        _isSubmitting = false;
      });
    }
  }

  void _nextQuestion() {
    if (_currentIndex < _questions.length - 1) {
      setState(() {
        _currentIndex++;
        _selectedOption = null;
        _lastResult = null;
      });
    }
  }

  void _prevQuestion() {
    if (_currentIndex > 0) {
      setState(() {
        _currentIndex--;
        _selectedOption = null;
        _lastResult = null;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Previous Year Questions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadQuestions,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _questions.isEmpty
              ? const Center(child: Text('No questions found.'))
              : Column(
                  children: [
                    _buildProgressBar(theme),
                    Expanded(
                      child: SingleChildScrollView(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildMetadataHeader(theme),
                            const SizedBox(height: 12),
                            _buildQuestionStem(theme),
                            const SizedBox(height: 16),
                            _buildOptionsList(theme),
                            const SizedBox(height: 16),
                            if (_lastResult != null) _buildResultCard(theme),
                          ],
                        ),
                      ),
                    ),
                    _buildBottomBar(theme),
                  ],
                ),
    );
  }

  Widget _buildProgressBar(ThemeData theme) {
    final progress = (_currentIndex + 1) / _questions.length;
    return LinearProgressIndicator(
      value: progress,
      minHeight: 4,
      backgroundColor: theme.colorScheme.surfaceContainerHighest,
      color: theme.colorScheme.primary,
    );
  }

  Widget _buildMetadataHeader(ThemeData theme) {
    final q = _questions[_currentIndex];
    return Row(
      children: [
        Chip(
          label: Text(
            '${q.year} • ${q.stage.toUpperCase()}',
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
          ),
          padding: EdgeInsets.zero,
        ),
        const SizedBox(width: 8),
        Chip(
          label: Text(
            '+${q.marks} / -${q.negativeMarks}',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: theme.colorScheme.error,
            ),
          ),
          padding: EdgeInsets.zero,
        ),
        const Spacer(),
        Text(
          'Q ${_currentIndex + 1} of ${_questions.length}',
          style: theme.textTheme.bodyMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  Widget _buildQuestionStem(ThemeData theme) {
    final q = _questions[_currentIndex];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (q.subtopicTitle != null)
          Text(
            q.subtopicTitle!,
            style: theme.textTheme.labelMedium?.copyWith(
              color: theme.colorScheme.primary,
              fontWeight: FontWeight.w600,
            ),
          ),
        const SizedBox(height: 4),
        Text(
          q.questionText,
          style: theme.textTheme.titleMedium?.copyWith(
            height: 1.4,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildOptionsList(ThemeData theme) {
    final q = _questions[_currentIndex];
    final isSubmitted = _lastResult != null;

    return Column(
      children: q.options.map((opt) {
        final isSelected = _selectedOption == opt.label;
        final isCorrectOpt = isSubmitted && opt.label.toUpperCase() == q.correctAnswer.toUpperCase();
        final isWrongSelected = isSubmitted && isSelected && !isCorrectOpt;

        Color? tileColor;
        BorderSide border = BorderSide.none;

        if (isSubmitted) {
          if (isCorrectOpt) {
            tileColor = Colors.green.withAlpha(40);
            border = BorderSide(color: Colors.green[700]!, width: 2);
          } else if (isWrongSelected) {
            tileColor = Colors.red.withAlpha(40);
            border = BorderSide(color: Colors.red[700]!, width: 2);
          }
        } else if (isSelected) {
          tileColor = theme.colorScheme.primaryContainer.withAlpha(120);
          border = BorderSide(color: theme.colorScheme.primary, width: 2);
        }

        return Container(
          margin: const EdgeInsets.only(bottom: 10),
          decoration: BoxDecoration(
            color: tileColor ?? theme.colorScheme.surfaceContainerHighest.withAlpha(60),
            borderRadius: BorderRadius.circular(12),
            border: Border.fromBorderSide(border),
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: isSubmitted
                  ? null
                  : () {
                      setState(() => _selectedOption = opt.label);
                    },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Row(
                  children: [
                    CircleAvatar(
                      radius: 14,
                      backgroundColor: isSelected
                          ? theme.colorScheme.primary
                          : theme.colorScheme.surfaceContainerHighest,
                      child: Text(
                        opt.label,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: isSelected
                              ? theme.colorScheme.onPrimary
                              : theme.colorScheme.onSurface,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(opt.text, style: theme.textTheme.bodyMedium),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildResultCard(ThemeData theme) {
    final res = _lastResult!;
    final isCorrect = res.isCorrect;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: isCorrect ? Colors.green.withAlpha(25) : Colors.red.withAlpha(25),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isCorrect ? Colors.green : Colors.red,
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isCorrect ? Icons.check_circle : Icons.cancel,
                color: isCorrect ? Colors.green[700] : Colors.red[700],
              ),
              const SizedBox(width: 8),
              Text(
                isCorrect
                    ? 'Correct (+${res.marksAwarded} Marks)'
                    : 'Incorrect (${res.marksAwarded} Marks Penalty)',
                style: theme.textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: isCorrect ? Colors.green[800] : Colors.red[800],
                ),
              ),
            ],
          ),
          if (res.errorType != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.orange.withAlpha(40),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                'Cognitive Diagnostic: ${res.errorType!.replaceAll('_', ' ').toUpperCase()}',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: Colors.deepOrange,
                ),
              ),
            ),
          ],
          const SizedBox(height: 10),
          Text(
            'Explanation:',
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            res.explanation,
            style: theme.textTheme.bodySmall?.copyWith(height: 1.35),
          ),
          if (res.sourceCitation != null) ...[
            const SizedBox(height: 8),
            Text(
              'Source: ${res.sourceCitation}',
              style: theme.textTheme.bodySmall?.copyWith(
                fontStyle: FontStyle.italic,
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildBottomBar(ThemeData theme) {
    final isSubmitted = _lastResult != null;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withAlpha(15),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        children: [
          OutlinedButton(
            onPressed: _currentIndex > 0 ? _prevQuestion : null,
            child: const Text('Previous'),
          ),
          const Spacer(),
          if (!isSubmitted)
            FilledButton(
              onPressed: _selectedOption != null && !_isSubmitting ? _submitCurrent : null,
              child: _isSubmitting
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Submit Answer'),
            )
          else
            FilledButton(
              onPressed: _currentIndex < _questions.length - 1 ? _nextQuestion : null,
              child: const Text('Next Question'),
            ),
        ],
      ),
    );
  }
}
