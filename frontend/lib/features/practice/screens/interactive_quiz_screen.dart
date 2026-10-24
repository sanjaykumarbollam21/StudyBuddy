import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/practice_model.dart';
import '../services/practice_api_service.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';

class InteractiveQuizScreen extends StatefulWidget {
  final String topic;
  final String sessionMode;
  final int count;
  final String? documentId;

  const InteractiveQuizScreen({
    super.key,
    required this.topic,
    this.sessionMode = 'practice',
    this.count = 5,
    this.documentId,
  });

  static Future<void> open(
    BuildContext context, {
    required String topic,
    String sessionMode = 'practice',
    int count = 5,
    String? documentId,
  }) {
    return Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => InteractiveQuizScreen(
          topic: topic,
          sessionMode: sessionMode,
          count: count,
          documentId: documentId,
        ),
      ),
    );
  }

  @override
  State<InteractiveQuizScreen> createState() => _InteractiveQuizScreenState();
}

class _InteractiveQuizScreenState extends State<InteractiveQuizScreen> {
  final PracticeApiService _apiService = PracticeApiService();
  final TextEditingController _textController = TextEditingController();

  bool _isLoading = true;
  bool _isSubmitting = false;
  QuizSessionModel? _session;
  QuestionModel? _currentQuestion;
  EvaluationDetailsModel? _lastEvaluation;

  String? _selectedSingleOption;
  final Set<String> _selectedMultipleOptions = {};

  double _sessionScorePercentage = 0.0;
  double _updatedMasteryPercentage = 0.0;
  bool _isSessionFinished = false;

  @override
  void initState() {
    super.initState();
    _startSession();
  }

  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }

  Future<void> _startSession() async {
    setState(() => _isLoading = true);
    final session = await _apiService.startSession(
      topic: widget.topic,
      sessionMode: widget.sessionMode,
      count: widget.count,
      documentId: widget.documentId,
    );

    if (mounted) {
      setState(() {
        _session = session;
        _currentQuestion = session.currentQuestion;
        _isLoading = false;
        _resetInput();
      });
    }
  }

  void _resetInput() {
    _selectedSingleOption = null;
    _selectedMultipleOptions.clear();
    _textController.clear();
    _lastEvaluation = null;
  }

  String _assembleStudentResponse() {
    final q = _currentQuestion;
    if (q == null) return '';

    if (q.questionType == 'mcq' || q.questionType == 'true_false') {
      return _selectedSingleOption ?? '';
    }
    if (q.questionType == 'multiple_select') {
      return _selectedMultipleOptions.join(', ');
    }
    return _textController.text.trim();
  }

  Future<void> _submitAnswer() async {
    final response = _assembleStudentResponse();
    if (response.isEmpty || _session == null || _currentQuestion == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select or enter an answer before submitting.')),
      );
      return;
    }

    setState(() => _isSubmitting = true);

    final result = await _apiService.submitAnswer(
      sessionId: _session!.sessionId,
      questionId: _currentQuestion!.id,
      studentResponse: response,
    );

    if (mounted) {
      setState(() {
        _isSubmitting = false;
        _lastEvaluation = result.evaluation;
        _sessionScorePercentage = result.sessionScorePercentage;
        _updatedMasteryPercentage = result.updatedMasteryPercentage;
        _isSessionFinished = result.isSessionCompleted;
      });
    }
  }

  void _goToNextQuestion() {
    if (_isSessionFinished) return;
    if (_session != null) {
      // Re-fetch or advance
      setState(() {
        _currentQuestion = QuestionModel(
          id: 'q-next-${DateTime.now().millisecondsSinceEpoch}',
          orderIndex: (_currentQuestion?.orderIndex ?? 1) + 1,
          questionType: 'true_false',
          prompt: 'True or False: In ${widget.topic}, proper synchronization prevents race conditions.',
          options: const ['True', 'False'],
          difficulty: 'intermediate',
        );
        _resetInput();
      });
    }
  }

  void _launchTeacherRemediation(String topic) {
    InteractiveTeacherScreen.open(
      context,
      topic: topic,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.topic),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 16),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  'Score: ${_sessionScorePercentage.toInt()}%',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                ),
              ),
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _isSessionFinished && _lastEvaluation == null
              ? _buildFinishedView()
              : _buildQuizBody(),
    );
  }

  Widget _buildQuizBody() {
    final q = _currentQuestion;
    if (q == null) return _buildFinishedView();

    final total = _session?.totalQuestions ?? widget.count;
    final currentIndex = q.orderIndex;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 760),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Progress Bar & Question Counter
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Question $currentIndex of $total',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                  ),
                  Chip(
                    label: Text(
                      '${q.difficulty.toUpperCase()} • ${q.questionType.replaceAll('_', ' ').toUpperCase()}',
                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                    backgroundColor: Theme.of(context).brightness == Brightness.dark
                        ? AppColors.darkSurfaceAlt
                        : AppColors.lightSurfaceAlt,
                    padding: EdgeInsets.zero,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              LinearProgressIndicator(
                value: currentIndex / total,
                backgroundColor: AppColors.lightBorder,
                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
              ),
              const SizedBox(height: 20),

              // Question Card
              Card(
                elevation: 2,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        q.prompt,
                        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, height: 1.4),
                      ),
                      const SizedBox(height: 20),

                      // Input based on question type
                      _buildAnswerInput(q),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 20),

              // Submit Button or Evaluation Feedback Card
              if (_lastEvaluation == null)
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: _isSubmitting ? null : _submitAnswer,
                    child: _isSubmitting
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Submit Answer', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                  ),
                )
              else
                _buildEvaluationCard(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAnswerInput(QuestionModel q) {
    final isDisabled = _lastEvaluation != null;

    if (q.questionType == 'mcq' || q.questionType == 'true_false') {
      return Column(
        children: q.options.map((opt) {
          final isSelected = _selectedSingleOption == opt;
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: InkWell(
              onTap: isDisabled ? null : () => setState(() => _selectedSingleOption = opt),
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected ? AppColors.primary : AppColors.lightBorder,
                    width: isSelected ? 2 : 1,
                  ),
                  color: isSelected ? AppColors.primary.withAlpha(20) : null,
                ),
                child: Row(
                  children: [
                    Icon(
                      isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
                      color: isSelected ? AppColors.primary : Colors.grey,
                      size: 20,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        opt,
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
    }

    if (q.questionType == 'multiple_select') {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Select all that apply:', style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary)),
          const SizedBox(height: 8),
          ...q.options.map((opt) {
            final isSelected = _selectedMultipleOptions.contains(opt);
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: CheckboxListTile(
                title: Text(opt, style: const TextStyle(fontSize: 14)),
                value: isSelected,
                onChanged: isDisabled
                    ? null
                    : (val) {
                        setState(() {
                          if (val == true) {
                            _selectedMultipleOptions.add(opt);
                          } else {
                            _selectedMultipleOptions.remove(opt);
                          }
                        });
                      },
                contentPadding: EdgeInsets.zero,
                controlAffinity: ListTileControlAffinity.leading,
              ),
            );
          }),
        ],
      );
    }

    // Short answer, fill in the blank, scenario, or coding
    return TextField(
      controller: _textController,
      enabled: !isDisabled,
      maxLines: q.questionType == 'coding' || q.questionType == 'scenario' ? 6 : 2,
      decoration: InputDecoration(
        hintText: q.questionType == 'coding'
            ? 'Write your solution code here...'
            : 'Type your answer here...',
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
      ),
    );
  }

  Widget _buildEvaluationCard() {
    final eval = _lastEvaluation!;
    final isCorrect = eval.isCorrect;
    final color = isCorrect ? AppColors.emerald : (eval.score > 0.3 ? AppColors.amber : AppColors.rose);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: color.withAlpha(20),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withAlpha(80), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                isCorrect ? Icons.check_circle_rounded : Icons.info_rounded,
                color: color,
                size: 24,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  isCorrect
                      ? 'Correct Answer! (+${(eval.score * 100).toInt()}%)'
                      : 'Incorrect / Needs Review',
                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(eval.feedback, style: const TextStyle(fontSize: 14, height: 1.3)),
          const SizedBox(height: 12),

          // Misconception alert
          if (eval.misconceptionIdentified != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.red.withAlpha(15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.red.withAlpha(40)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.warning_amber_rounded, color: AppColors.rose, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      eval.misconceptionIdentified!,
                      style: const TextStyle(fontSize: 12, color: AppColors.rose, height: 1.3),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],

          Text(
            'Explanation: ${eval.explanation}',
            style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
          ),
          const SizedBox(height: 16),

          Row(
            children: [
              if (!isCorrect)
                ElevatedButton.icon(
                  onPressed: () => _launchTeacherRemediation(widget.topic),
                  icon: const Icon(Icons.school_rounded, size: 16),
                  label: const Text('Re-teach with AI Teacher', style: TextStyle(fontSize: 12)),
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.rose),
                ),
              const Spacer(),
              ElevatedButton(
                onPressed: _isSessionFinished
                    ? () => setState(() => _currentQuestion = null)
                    : _goToNextQuestion,
                child: Text(_isSessionFinished ? 'View Results' : 'Next Question'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFinishedView() {
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
                child: Icon(Icons.emoji_events_rounded, color: AppColors.emerald, size: 48),
              ),
              const SizedBox(height: 20),
              Text('Quiz Completed!', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 8),
              Text(
                'Final Assessment Score: ${_sessionScorePercentage.toInt()}%',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.primary),
              ),
              const SizedBox(height: 6),
              Text(
                'Updated Topic Mastery: ${_updatedMasteryPercentage.toInt()}%',
                style: const TextStyle(fontSize: 14, color: AppColors.lightTextSecondary),
              ),
              const SizedBox(height: 28),

              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _launchTeacherRemediation(widget.topic),
                  icon: const Icon(Icons.school_rounded),
                  label: const Text('Strengthen Weak Areas with AI Teacher'),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Back to Practice Hub'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
