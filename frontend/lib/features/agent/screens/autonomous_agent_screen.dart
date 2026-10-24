import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/agent_task_model.dart';
import '../services/agent_api_service.dart';

class AutonomousAgentScreen extends StatefulWidget {
  const AutonomousAgentScreen({super.key});

  @override
  State<AutonomousAgentScreen> createState() => _AutonomousAgentScreenState();
}

class _AutonomousAgentScreenState extends State<AutonomousAgentScreen> {
  final AgentApiService _apiService = AgentApiService();
  final TextEditingController _chatController = TextEditingController();

  AgentTaskModel? _currentTask;
  bool _isLoading = true;
  bool _isExecuting = false;
  int _selectedMinutes = 60;
  String? _executionSummary;
  String? _chatReply;

  @override
  void initState() {
    super.initState();
    _loadEvaluation();
  }

  @override
  void dispose() {
    _chatController.dispose();
    super.dispose();
  }

  Future<void> _loadEvaluation() async {
    setState(() => _isLoading = true);
    // Check if there is an active ongoing or paused task from previous session
    final active = await _apiService.getActiveTask();
    if (active != null && (active.currentState == 'paused' || active.currentState == 'executing')) {
      if (mounted) {
        setState(() {
          _currentTask = active;
          _isLoading = false;
          _executionSummary = null;
        });
        return;
      }
    }

    final task = await _apiService.evaluateState(availableMinutes: _selectedMinutes);
    if (mounted) {
      setState(() {
        _currentTask = task;
        _isLoading = false;
        _executionSummary = null;
      });
    }
  }

  Future<void> _pauseCurrentTask() async {
    if (_currentTask == null) return;
    final paused = await _apiService.pauseTask(_currentTask!.id);
    if (mounted && paused != null) {
      setState(() {
        _currentTask = paused;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Study session paused. You can resume anytime!'),
          backgroundColor: AppColors.amber,
        ),
      );
    }
  }

  Future<void> _resumeCurrentTask() async {
    if (_currentTask == null) return;
    setState(() => _isExecuting = true);
    final resumeInfo = await _apiService.resumeTask(_currentTask!.id);
    if (mounted) {
      setState(() {
        _currentTask!.currentState = 'executing';
        _isExecuting = false;
        _executionSummary = resumeInfo?['status_summary'] as String? ?? 'Resumed active session.';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(resumeInfo?['status_summary'] as String? ?? 'Resumed active session.'),
          backgroundColor: AppColors.emerald,
        ),
      );
    }
  }

  Future<void> _executeCurrentTask() async {
    if (_currentTask == null) return;
    setState(() => _isExecuting = true);

    final res = await _apiService.executeTask(_currentTask!.id);
    if (mounted) {
      setState(() {
        _isExecuting = false;
        _currentTask!.currentState = 'completed';
        _currentTask!.currentStepIndex = _currentTask!.proposedActions.length;
        _executionSummary = res['execution_summary'] as String? ?? 'Task completed successfully.';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Autonomous study session executed and mastery calibrated!'),
          backgroundColor: AppColors.emerald,
        ),
      );
    }
  }

  void _showExplainabilityDialog() {
    if (_currentTask == null) return;
    final b = _currentTask!.explanationBreakdown;
    final topic = b['top_topic'] ?? _currentTask!.goal;
    final mastery = b['mastery_percentage'] ?? 48.0;
    final examWeight = b['exam_weight'] ?? 1.8;
    final days = b['days_until_exam'] ?? 5;
    final revisions = b['due_revisions'] ?? 3;

    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.psychology_alt_rounded, color: AppColors.primary, size: 28),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text('Why Did Study Buddy Choose This?', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(
              'Autonomous Decision Telemetry for "$topic":',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
            ),
            const SizedBox(height: 12),
            _buildMetricRow('Current Topic Mastery', '$mastery% (Target: 80%)', AppColors.rose),
            _buildMetricRow('Exam Blueprint Importance', '${examWeight}x relative weight', AppColors.amber),
            _buildMetricRow('Exam Countdown', '$days days remaining', AppColors.primary),
            _buildMetricRow('Overdue Spaced Revisions', '$revisions items needing active recall', AppColors.amber),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.primary.withAlpha(20),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                'Conclusion: Remediating Deadlocks yields the highest score gain per study minute, preventing forgetting on overdue retention items.',
                style: TextStyle(fontSize: 12, height: 1.4),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricRow(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(label, style: const TextStyle(fontSize: 13, color: AppColors.lightTextSecondary)),
          ),
          const SizedBox(width: 8),
          Text(value, style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }

  Future<void> _handleChatSubmit(String prompt) async {
    if (prompt.trim().isEmpty) return;
    _chatController.clear();
    setState(() => _isLoading = true);

    final res = await _apiService.chatWithAgent(prompt, availableMinutes: _selectedMinutes);
    if (mounted) {
      setState(() {
        _chatReply = res.reply;
        if (res.suggestedTask != null) {
          _currentTask = res.suggestedTask;
        }
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Autonomous Study Agent', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.emerald.withAlpha(25),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.emerald.withAlpha(80)),
            ),
            child: const Row(
              children: [
                Icon(Icons.circle, color: AppColors.emerald, size: 8),
                SizedBox(width: 6),
                Text('Active Orchestrator', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.emerald)),
              ],
            ),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 800),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Time Allocation Selector
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Available Study Time:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          Wrap(
                            spacing: 8,
                            children: [15, 30, 60, 90].map((mins) {
                              final isSelected = _selectedMinutes == mins;
                              return ChoiceChip(
                                label: Text('${mins}m'),
                                selected: isSelected,
                                onSelected: (sel) {
                                  if (sel) {
                                    setState(() => _selectedMinutes = mins);
                                    _loadEvaluation();
                                  }
                                },
                                selectedColor: AppColors.primary,
                                labelStyle: TextStyle(
                                  color: isSelected ? Colors.white : AppColors.lightTextSecondary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
                              );
                            }).toList(),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Task Recommendation Card
                      if (_currentTask != null) ...[
                        Card(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16),
                            side: BorderSide(
                              color: _currentTask!.priority == 'critical'
                                  ? AppColors.rose.withAlpha(120)
                                  : AppColors.primary.withAlpha(80),
                            ),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                      decoration: BoxDecoration(
                                        color: AppColors.rose.withAlpha(25),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        _currentTask!.priority.toUpperCase(),
                                        style: const TextStyle(
                                          color: AppColors.rose,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 11,
                                        ),
                                      ),
                                    ),
                                    const Spacer(),
                                    Text(
                                      '${_currentTask!.allocatedMinutes} min allocated',
                                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  _currentTask!.goal,
                                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  _currentTask!.reason,
                                  style: const TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
                                ),
                                const SizedBox(height: 20),

                                // Resumption Banner
                                if (_currentTask!.currentState == 'paused' || (_currentTask!.currentStepIndex > 0 && _currentTask!.currentState != 'completed'))
                                  Container(
                                    margin: const EdgeInsets.only(bottom: 14),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: AppColors.amber.withAlpha(25),
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(color: AppColors.amber.withAlpha(100)),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.pause_circle_filled_rounded, color: AppColors.amber, size: 20),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            'Active session paused: Completed Step ${_currentTask!.currentStepIndex} of ${_currentTask!.proposedActions.length}',
                                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.amber),
                                          ),
                                        ),
                                        TextButton(
                                          onPressed: _resumeCurrentTask,
                                          child: const Text('Resume', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                        ),
                                      ],
                                    ),
                                  ),

                                const Text('Orchestrated Actions:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                const SizedBox(height: 10),
                                ..._currentTask!.proposedActions.map((step) {
                                  final isDone = step.step <= _currentTask!.currentStepIndex;
                                  final isCurrent = step.step == _currentTask!.currentStepIndex + 1 && _currentTask!.currentState == 'executing';
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 8),
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: isDone
                                          ? AppColors.emerald.withAlpha(15)
                                          : isCurrent
                                              ? AppColors.primary.withAlpha(20)
                                              : AppColors.primary.withAlpha(10),
                                      borderRadius: BorderRadius.circular(10),
                                      border: isCurrent ? Border.all(color: AppColors.primary) : null,
                                    ),
                                    child: Row(
                                      children: [
                                        CircleAvatar(
                                          radius: 12,
                                          backgroundColor: isDone
                                              ? AppColors.emerald
                                              : isCurrent
                                                  ? AppColors.primary
                                                  : AppColors.primary.withAlpha(120),
                                          child: isDone
                                              ? const Icon(Icons.check, size: 14, color: Colors.white)
                                              : Text(
                                                  '${step.step}',
                                                  style: const TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold),
                                                ),
                                        ),
                                        const SizedBox(width: 12),
                                        Expanded(
                                          child: Column(
                                            crossAxisAlignment: CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                step.description,
                                                style: TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w600,
                                                  decoration: isDone ? TextDecoration.lineThrough : null,
                                                  color: isDone ? AppColors.lightTextSecondary : null,
                                                ),
                                              ),
                                              Text('Engine: ${step.engine}', style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary)),
                                            ],
                                          ),
                                        ),
                                        if (step.durationMins > 0)
                                          Text('${step.durationMins}m', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                                      ],
                                    ),
                                  );
                                }),

                                const SizedBox(height: 16),

                                // Action Buttons
                                Row(
                                  children: [
                                    if (_currentTask!.currentState == 'paused') ...[
                                      Expanded(
                                        child: ElevatedButton.icon(
                                          onPressed: _resumeCurrentTask,
                                          icon: const Icon(Icons.play_arrow_rounded, color: Colors.white),
                                          label: const Text('Resume Session', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: AppColors.emerald,
                                            padding: const EdgeInsets.symmetric(vertical: 14),
                                          ),
                                        ),
                                      ),
                                    ] else ...[
                                      Expanded(
                                        child: ElevatedButton.icon(
                                          onPressed: _isExecuting || _currentTask!.currentState == 'completed'
                                              ? null
                                              : _executeCurrentTask,
                                          icon: _isExecuting
                                              ? const SizedBox(
                                                  width: 14,
                                                  height: 14,
                                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                                )
                                              : const Icon(Icons.play_arrow_rounded, color: Colors.white),
                                          label: Text(
                                            _currentTask!.currentState == 'completed'
                                                ? 'Session Completed'
                                                : (_isExecuting ? 'Orchestrating...' : 'Start Autonomous Session'),
                                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                          ),
                                          style: ElevatedButton.styleFrom(
                                            backgroundColor: AppColors.primary,
                                            padding: const EdgeInsets.symmetric(vertical: 14),
                                          ),
                                        ),
                                      ),
                                    ],
                                    if (_currentTask!.currentState == 'executing') ...[
                                      const SizedBox(width: 8),
                                      IconButton.filled(
                                        onPressed: _pauseCurrentTask,
                                        icon: const Icon(Icons.pause_rounded),
                                        style: IconButton.styleFrom(backgroundColor: AppColors.amber),
                                      ),
                                    ],
                                    const SizedBox(width: 10),
                                    OutlinedButton.icon(
                                      onPressed: _showExplainabilityDialog,
                                      icon: const Icon(Icons.help_outline_rounded, size: 16),
                                      label: const Text('Why this?'),
                                      style: OutlinedButton.styleFrom(
                                        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 14),
                                      ),
                                    ),
                                  ],
                                ),

                                if (_executionSummary != null) ...[
                                  const SizedBox(height: 16),
                                  Container(
                                    padding: const EdgeInsets.all(12),
                                    decoration: BoxDecoration(
                                      color: AppColors.emerald.withAlpha(20),
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(color: AppColors.emerald.withAlpha(80)),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.check_circle_rounded, color: AppColors.emerald),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Text(
                                            _executionSummary!,
                                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.emerald),
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

                      const SizedBox(height: 24),

                      // Conversational Agent Interface
                      const Text('Talk to Autonomous Agent', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          'I have 1 hour, prepare me for exam',
                          'Fix my weakest topic',
                          'Review due revision items',
                        ].map((prompt) {
                          return ActionChip(
                            label: Text(prompt, style: const TextStyle(fontSize: 12)),
                            onPressed: () => _handleChatSubmit(prompt),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 12),

                      if (_chatReply != null)
                        Container(
                          margin: const EdgeInsets.only(bottom: 12),
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.primary.withAlpha(15),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(_chatReply!, style: const TextStyle(fontSize: 13, height: 1.4)),
                        ),

                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _chatController,
                              decoration: const InputDecoration(
                                hintText: 'Ask agent to take care of study tasks...',
                                border: OutlineInputBorder(),
                                contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                              ),
                              onSubmitted: _handleChatSubmit,
                            ),
                          ),
                          const SizedBox(width: 8),
                          IconButton.filled(
                            onPressed: () => _handleChatSubmit(_chatController.text),
                            icon: const Icon(Icons.send_rounded),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
    );
  }
}
