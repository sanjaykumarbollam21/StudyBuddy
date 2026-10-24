import 'package:flutter/material.dart';
import '../models/competitive_exam_models.dart';
import '../services/competitive_exam_service.dart';

class MainsAnswerWritingScreen extends StatefulWidget {
  const MainsAnswerWritingScreen({super.key});

  @override
  State<MainsAnswerWritingScreen> createState() =>
      _MainsAnswerWritingScreenState();
}

class _MainsAnswerWritingScreenState extends State<MainsAnswerWritingScreen> {
  final CompetitiveExamService _service = CompetitiveExamService();
  final TextEditingController _questionCtrl = TextEditingController(
    text:
        'Critically analyze the role of Judicial Review in safeguarding constitutionalism in India. (150 words / 10 marks)',
  );
  final TextEditingController _answerCtrl = TextEditingController();

  int _wordLimit = 150;
  bool _isEvaluating = false;
  MainsAnswerEvaluationModel? _evaluation;

  @override
  void dispose() {
    _questionCtrl.dispose();
    _answerCtrl.dispose();
    super.dispose();
  }

  int get _currentWordCount {
    final text = _answerCtrl.text.trim();
    if (text.isEmpty) return 0;
    return text.split(RegExp(r'\s+')).length;
  }

  Future<void> _submitForEvaluation() async {
    if (_answerCtrl.text.trim().isEmpty) return;
    setState(() => _isEvaluating = true);

    final res = await _service.evaluateMainsAnswer(
      questionText: _questionCtrl.text,
      studentAnswerText: _answerCtrl.text,
      wordLimit: _wordLimit,
      allocatedMarks: 10.0,
    );

    if (mounted) {
      setState(() {
        _evaluation = res;
        _isEvaluating = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final count = _currentWordCount;
    final isOverLimit = count > (_wordLimit * 1.15);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mains Answer Writing Evaluator'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildQuestionCard(theme),
            const SizedBox(height: 16),
            _buildAnswerEditor(theme, count, isOverLimit),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: FilledButton.icon(
                icon: const Icon(Icons.analytics_outlined),
                label: _isEvaluating
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Evaluate Answer across 8 Rubrics'),
                onPressed: _answerCtrl.text.trim().isEmpty || _isEvaluating
                    ? null
                    : _submitForEvaluation,
              ),
            ),
            if (_evaluation != null) ...[
              const SizedBox(height: 20),
              _buildEvaluationResults(theme),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildQuestionCard(ThemeData theme) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.help_outline, size: 20, color: Colors.teal),
                const SizedBox(width: 8),
                Text(
                  'Mains Question Prompt',
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                DropdownButton<int>(
                  value: _wordLimit,
                  underline: const SizedBox.shrink(),
                  items: const [
                    DropdownMenuItem(value: 150, child: Text('150 Words (10M)')),
                    DropdownMenuItem(value: 250, child: Text('250 Words (15M)')),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _wordLimit = val);
                  },
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _questionCtrl,
              maxLines: 2,
              decoration: const InputDecoration(
                border: InputBorder.none,
                isDense: true,
              ),
              style: theme.textTheme.bodyMedium?.copyWith(fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnswerEditor(ThemeData theme, int count, bool isOverLimit) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Row(
              children: [
                Text(
                  'Your Answer Draft',
                  style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Text(
                  '$count / $_wordLimit words',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: isOverLimit ? Colors.red : theme.colorScheme.onSurfaceVariant,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _answerCtrl,
              maxLines: 10,
              decoration: const InputDecoration(
                hintText:
                    'Draft your answer here...\n\nInclude:\n• Introduction & definition\n• Subheadings & Constitutional Articles\n• Balanced critique & examples\n• Forward-looking Conclusion / Way Forward',
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEvaluationResults(ThemeData theme) {
    final e = _evaluation!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          color: theme.colorScheme.primaryContainer.withAlpha(80),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Row(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Score: ${e.marksObtained.toStringAsFixed(1)} / ${e.totalMarks.toStringAsFixed(0)}',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                    Text(
                      '${e.scorePercentage.round()}% Quality Benchmark',
                      style: theme.textTheme.bodySmall,
                    ),
                  ],
                ),
                const Spacer(),
                Chip(
                  label: Text('${e.wordCount} Words'),
                  backgroundColor: theme.colorScheme.surface,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          '8-Rubric Pedagogical Breakdown',
          style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        ...e.rubricBreakdown.entries.map((entry) {
          final label = entry.key.replaceAll('_', ' ').toUpperCase();
          final val = entry.value;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                    Text('${val.round()}%', style: const TextStyle(fontSize: 11)),
                  ],
                ),
                const SizedBox(height: 2),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: val / 100.0,
                    minHeight: 6,
                    color: val >= 65 ? Colors.green[700] : Colors.orange[800],
                    backgroundColor: theme.colorScheme.surfaceContainerHighest,
                  ),
                ),
              ],
            ),
          );
        }),
        const SizedBox(height: 16),
        if (e.strengths.isNotEmpty) ...[
          Text('Key Strengths:', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          ...e.strengths.map((s) => Text('• $s', style: theme.textTheme.bodySmall)),
          const SizedBox(height: 12),
        ],
        if (e.missingDimensions.isNotEmpty) ...[
          Text('Missing Dimensions to Elevate Score:', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold, color: Colors.deepOrange)),
          const SizedBox(height: 4),
          ...e.missingDimensions.map((m) => Text('• $m', style: theme.textTheme.bodySmall)),
          const SizedBox(height: 12),
        ],
        Text('Model Answer Outline & Structure:', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 4),
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: theme.colorScheme.surfaceContainerHighest.withAlpha(80),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(e.modelOutline, style: theme.textTheme.bodySmall?.copyWith(height: 1.4)),
        ),
      ],
    );
  }
}
