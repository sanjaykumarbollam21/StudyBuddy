import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import 'tutor_sheet.dart';

class ProgressTab extends StatelessWidget {
  const ProgressTab({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Learning Progress & Mastery', style: Theme.of(context).textTheme.headlineMedium),
              const SizedBox(height: 6),
              const Text(
                'Diagnostic metrics, conceptual retention rates, and smart study recommendations.',
                style: TextStyle(color: AppColors.lightTextSecondary),
              ),
              const SizedBox(height: 24),

              // KPI Metric Cards
              Row(
                children: [
                  _MetricCard(title: 'Study Time', value: '14.5 hrs', subtitle: 'This week', icon: Icons.schedule_rounded, color: AppColors.primary),
                  const SizedBox(width: 12),
                  _MetricCard(title: 'Concepts Mastered', value: '18', subtitle: '72% overall', icon: Icons.verified_rounded, color: AppColors.emerald),
                  const SizedBox(width: 12),
                  _MetricCard(title: 'Study Streak', value: '5 Days', subtitle: 'Top 10%', icon: Icons.local_fire_department_rounded, color: AppColors.amber),
                ],
              ),
              const SizedBox(height: 28),

              // AI Smart Recommendation Card (Section 25)
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: AppColors.primary.withAlpha(20),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.primary.withAlpha(80)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.psychology_rounded, color: AppColors.primary, size: 24),
                        SizedBox(width: 10),
                        Text(
                          'Study Buddy Teacher Recommendation',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.primary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      '“Before proceeding to Banker’s Deadlock Avoidance, I strongly recommend revising Semaphore Wait & Signal primitives. Your last two practice answers revealed an inversion misconception that could make Deadlock calculations difficult.”',
                      style: TextStyle(fontSize: 14, height: 1.4, fontStyle: FontStyle.italic),
                    ),
                    const SizedBox(height: 14),
                    ElevatedButton.icon(
                      onPressed: () {
                        TutorSheet.show(
                          context,
                          initialPrompt: 'Study Buddy, teach me the Semaphore Wait & Signal primitives to fix my misconception.',
                        );
                      },
                      icon: const Icon(Icons.school_rounded, size: 18),
                      label: const Text('Start 10-Minute Focused Revision'),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 28),

              // Weak Areas Detected (Section 19)
              const Text('Areas Requiring Attention', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),

              _WeakAreaCard(
                concept: 'Process Synchronization: Circular Wait Condition',
                subject: 'Operating Systems',
                accuracy: '38% Mastery',
                reason: 'Repeated confusion on dining philosophers deadlock states.',
              ),
              const SizedBox(height: 10),

              _WeakAreaCard(
                concept: 'Call Stack Allocation in Deep Recursion',
                subject: 'Python Programming',
                accuracy: '46% Mastery',
                reason: 'Struggled with stack overflow boundary questions.',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String title;
  final String value;
  final String subtitle;
  final IconData icon;
  final Color color;

  const _MetricCard({
    required this.title,
    required this.value,
    required this.subtitle,
    required this.icon,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(height: 12),
              Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 2),
              Text(title, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
              Text(subtitle, style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary)),
            ],
          ),
        ),
      ),
    );
  }
}

class _WeakAreaCard extends StatelessWidget {
  final String concept;
  final String subject;
  final String accuracy;
  final String reason;

  const _WeakAreaCard({
    required this.concept,
    required this.subject,
    required this.accuracy,
    required this.reason,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: const CircleAvatar(
          backgroundColor: AppColors.roseLight,
          child: Icon(Icons.warning_amber_rounded, color: AppColors.rose),
        ),
        title: Text(concept, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 2),
            Text('$subject • $accuracy', style: const TextStyle(fontSize: 12, color: AppColors.rose, fontWeight: FontWeight.w600)),
            const SizedBox(height: 2),
            Text(reason, style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary)),
          ],
        ),
        trailing: OutlinedButton(
          onPressed: () {
            TutorSheet.show(
              context,
              initialPrompt: 'Help me master "$concept". Give me intuitive examples.',
            );
          },
          child: const Text('Review', style: TextStyle(fontSize: 12)),
        ),
      ),
    );
  }
}
