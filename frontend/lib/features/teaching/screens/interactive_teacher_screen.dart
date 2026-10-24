import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../voice/screens/voice_teacher_screen.dart';
import '../models/teaching_model.dart';
import '../services/teaching_api_service.dart';

class InteractiveTeacherScreen extends StatefulWidget {
  final String topic;
  final String? subject;
  final String? documentId;
  final String? documentName;
  final String? sessionId;
  final TeachingApiService? apiService;

  const InteractiveTeacherScreen({
    super.key,
    required this.topic,
    this.subject,
    this.documentId,
    this.documentName,
    this.sessionId,
    this.apiService,
  });

  static Future<void> open(
    BuildContext context, {
    required String topic,
    String? subject,
    String? documentId,
    String? documentName,
    String? sessionId,
    TeachingApiService? apiService,
  }) {
    return Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => InteractiveTeacherScreen(
          topic: topic,
          subject: subject,
          documentId: documentId,
          documentName: documentName,
          sessionId: sessionId,
          apiService: apiService,
        ),
      ),
    );
  }

  @override
  State<InteractiveTeacherScreen> createState() => _InteractiveTeacherScreenState();
}

class _InteractiveTeacherScreenState extends State<InteractiveTeacherScreen> {
  late final TeachingApiService _apiService;
  final TextEditingController _answerController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  bool _isLoading = true;
  bool _isSubmitting = false;
  String? _sessionId;
  double _masteryScore = 0.0;
  int _currentStep = 1;
  int _totalSteps = 3;
  bool _isCompleted = false;

  final List<TeachingTurnModel> _history = [];
  TeachingTurnModel? _activeTurn;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService ?? TeachingApiService();
    _startSession();
  }

  @override
  void dispose() {
    _answerController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _startSession() async {
    setState(() => _isLoading = true);
    try {
      if (widget.sessionId != null) {
        final detail = await _apiService.getSession(widget.sessionId!);
        if (detail != null && detail.turns.isNotEmpty) {
          if (!mounted) return;
          setState(() {
            _sessionId = detail.sessionId;
            _history.clear();
            _history.addAll(detail.turns);
            _activeTurn = detail.turns.last;
            _masteryScore = detail.masteryScore;
            _currentStep = detail.currentStepIndex + 1;
            _isLoading = false;
          });
          _scrollToBottom();
          return;
        }
      }

      final turn = await _apiService.startSession(
        topic: widget.topic,
        subject: widget.subject,
        documentId: widget.documentId,
      );

      if (!mounted) return;
      setState(() {
        _sessionId = turn.sessionId;
        _activeTurn = turn;
        _history.add(turn);
        _masteryScore = turn.masteryPercentage;
        _currentStep = turn.currentStepNumber;
        _totalSteps = turn.totalSteps;
        _isLoading = false;
      });
      _scrollToBottom();
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
    }
  }

  Future<void> _submitResponse(String text, {String actionType = 'answer'}) async {
    final clean = text.trim();
    if (clean.isEmpty || _isSubmitting || _sessionId == null) return;

    setState(() => _isSubmitting = true);

    try {
      final turn = await _apiService.submitStudentTurn(
        sessionId: _sessionId!,
        answer: clean,
        actionType: actionType,
      );

      _answerController.clear();
      if (!mounted) return;
      setState(() {
        _activeTurn = turn;
        _history.add(turn);
        _masteryScore = turn.masteryPercentage;
        _currentStep = turn.currentStepNumber;
        _totalSteps = turn.totalSteps;
        _isCompleted = turn.isLessonCompleted;
        _isSubmitting = false;
      });
      _scrollToBottom();
    } catch (_) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      _answerController.text = clean;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Failed to submit response. Please retry.'),
          action: SnackBarAction(
            label: 'Retry',
            onPressed: () => _submitResponse(clean, actionType: actionType),
          ),
        ),
      );
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.topic,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            Text(
              widget.documentName != null
                  ? 'Grounded in: ${widget.documentName}'
                  : (widget.subject ?? 'Socratic Teaching Session'),
              style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.mic_rounded, color: AppColors.primary),
            tooltip: 'Switch to Voice Teacher Mode',
            onPressed: () {
              VoiceTeacherScreen.open(
                context,
                topic: widget.topic,
                subject: widget.subject,
                documentId: widget.documentId,
                documentName: widget.documentName,
              );
            },
          ),
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Chip(
              backgroundColor: AppColors.emerald.withAlpha(25),
              side: BorderSide(color: AppColors.emerald.withAlpha(80)),
              avatar: const Icon(Icons.bolt_rounded, size: 16, color: AppColors.emerald),
              label: Text(
                'Mastery: ${_masteryScore.round()}%',
                style: const TextStyle(
                  color: AppColors.emerald,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(6),
          child: LinearProgressIndicator(
            value: _totalSteps > 0 ? (_currentStep / _totalSteps).clamp(0.0, 1.0) : 0.3,
            backgroundColor: AppColors.primary.withAlpha(20),
            valueColor: const AlwaysStoppedAnimation<Color>(AppColors.primary),
          ),
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Teaching turn history list
                Expanded(
                  child: ListView.separated(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(18),
                    itemCount: _history.length,
                    separatorBuilder: (context, index) => const SizedBox(height: 18),
                    itemBuilder: (context, index) {
                      final turn = _history[index];
                      return _TeachingTurnCard(turn: turn, isLatest: index == _history.length - 1);
                    },
                  ),
                ),

                // Interactive Bottom Answer Input Bar
                _buildInputBar(isDark),
              ],
            ),
    );
  }

  Widget _buildInputBar(bool isDark) {
    final actions = _activeTurn?.suggestedActions ?? [];

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        border: Border(
          top: BorderSide(color: isDark ? AppColors.darkBorder : AppColors.lightBorder),
        ),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Suggested action pills
          if (actions.isNotEmpty && !_isCompleted) ...[
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: actions.map((act) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8, bottom: 10),
                    child: ActionChip(
                      label: Text(act, style: const TextStyle(fontSize: 12)),
                      backgroundColor: AppColors.primary.withAlpha(15),
                      side: BorderSide(color: AppColors.primary.withAlpha(50)),
                      onPressed: () => _submitResponse(act),
                    ),
                  );
                }).toList(),
              ),
            ),
          ],

          // Text Field & Submit Button
          if (!_isCompleted)
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _answerController,
                    decoration: InputDecoration(
                      hintText: 'Answer the question or share your thought...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                    ),
                    onSubmitted: (val) => _submitResponse(val),
                  ),
                ),
                const SizedBox(width: 10),
                CircleAvatar(
                  backgroundColor: AppColors.primary,
                  radius: 22,
                  child: _isSubmitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : IconButton(
                          icon: const Icon(Icons.send_rounded, color: Colors.white, size: 18),
                          onPressed: () => _submitResponse(_answerController.text),
                        ),
                ),
              ],
            )
          else
            Center(
              child: ElevatedButton.icon(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.check_circle_rounded),
                label: const Text('Return to Materials'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.emerald,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _TeachingTurnCard extends StatelessWidget {
  final TeachingTurnModel turn;
  final bool isLatest;

  const _TeachingTurnCard({required this.turn, required this.isLatest});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 1. Evaluation result banner (if this turn evaluated an answer)
        if (turn.evaluation != null) ...[
          _EvaluationBanner(eval: turn.evaluation!),
          const SizedBox(height: 12),
        ],

        // 2. Structured Teaching Card
        Card(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(
              color: isLatest ? AppColors.primary.withAlpha(80) : Colors.transparent,
              width: 1.5,
            ),
          ),
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Step badge & title
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppColors.primary.withAlpha(20),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        'Step ${turn.currentStepNumber} of ${turn.totalSteps}',
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold,
                          fontSize: 11,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (turn.conceptTitle != null)
                      Expanded(
                        child: Text(
                          turn.conceptTitle!,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 14),

                // Teacher message / explanation
                Text(
                  turn.teacherMessage,
                  style: const TextStyle(fontSize: 14, height: 1.5),
                ),

                // Source citation pill if grounded in student documents
                if (turn.sourceCitation != null) ...[
                  const SizedBox(height: 14),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: AppColors.emerald.withAlpha(15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.emerald.withAlpha(50)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.menu_book_rounded, size: 14, color: AppColors.emerald),
                        const SizedBox(width: 6),
                        Text(
                          'From: ${turn.sourceCitation!['document_name']} (Page ${turn.sourceCitation!['page_number']})',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: AppColors.emerald,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _EvaluationBanner extends StatelessWidget {
  final TeachingEvaluationModel eval;

  const _EvaluationBanner({required this.eval});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    IconData icon;
    String title;

    if (eval.isCorrect) {
      bg = AppColors.emerald.withAlpha(20);
      fg = AppColors.emerald;
      icon = Icons.check_circle_rounded;
      title = 'Concept Understood! Mastery ↑';
    } else if (eval.verdict == 'misconception') {
      bg = AppColors.rose.withAlpha(20);
      fg = AppColors.rose;
      icon = Icons.lightbulb_outline_rounded;
      title = 'Common Misconception Identified';
    } else {
      bg = AppColors.sky.withAlpha(20);
      fg = AppColors.sky;
      icon = Icons.info_outline_rounded;
      title = 'Let\'s Clarify Together';
    }

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: fg.withAlpha(80)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: fg, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(color: fg, fontWeight: FontWeight.bold, fontSize: 13),
                ),
                const SizedBox(height: 2),
                Text(
                  eval.feedback,
                  style: const TextStyle(fontSize: 12, height: 1.4),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
