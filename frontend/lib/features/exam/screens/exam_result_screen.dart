import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/exam_model.dart';
import '../../teaching/screens/interactive_teacher_screen.dart';

class ExamResultScreen extends StatelessWidget {
  final ExamResultModel result;

  const ExamResultScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final da = result.cognitiveDiagnosis;
    final readiness = result.readiness;
    final topicAnalysis = result.topicAnalysis;
    final remediation = result.remediationAction;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Exam Intelligence & Diagnosis'),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.close_rounded),
            tooltip: 'Return to dashboard',
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Score & Readiness Dual Card
              _buildScoreAndReadinessHero(context, readiness),

              const SizedBox(height: 20),

              // Cognitive Diagnostic Card ("Your biggest problem isn't memorization...")
              _buildCognitiveDiagnosticCard(context, da),

              const SizedBox(height: 20),

              // Closed Loop Reteach CTA Banner
              _buildRemediationBanner(context, remediation),

              const SizedBox(height: 24),

              // Topic-by-Topic Visual Breakdown
              _buildTopicBreakdownSection(context, topicAnalysis),

              const SizedBox(height: 24),

              // Multi-Factor Readiness Breakdown
              _buildReadinessDimensionsSection(context, readiness),

              const SizedBox(height: 30),

              // Bottom Actions
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: const Text('Back to Dashboard', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () => _launchSocraticReteach(context, remediation),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      icon: const Icon(Icons.auto_stories_rounded, size: 18),
                      label: Text(remediation.ctaTitle, style: const TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScoreAndReadinessHero(BuildContext context, ExamReadinessDetailModel readiness) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [
            AppColors.primaryDark,
            AppColors.primary,
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withAlpha(50),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            alignment: WrapAlignment.spaceBetween,
            crossAxisAlignment: WrapCrossAlignment.center,
            spacing: 8,
            runSpacing: 6,
            children: [
              Text(
                result.title.toUpperCase(),
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.8,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withAlpha(35),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  readiness.readinessCategory.toUpperCase(),
                  style: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              // Overall Score Block
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('OVERALL SCORE', style: TextStyle(color: Colors.white70, fontSize: 11)),
                    const SizedBox(height: 4),
                    Text(
                      '${result.scorePercentage.toInt()}%',
                      style: const TextStyle(color: Colors.white, fontSize: 36, fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${result.marksObtained.toStringAsFixed(1)} / ${result.totalMarks.toInt()} Marks',
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
              Container(width: 1, height: 60, color: Colors.white24),
              const SizedBox(width: 20),
              // Estimated Readiness Block
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('ESTIMATED READINESS', style: TextStyle(color: Colors.white70, fontSize: 11)),
                    const SizedBox(height: 4),
                    Text(
                      '${readiness.readinessPercentage.toInt()}%',
                      style: const TextStyle(color: AppColors.amber, fontSize: 36, fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Negative Marks: -${result.negativeMarksDeducted}',
                      style: const TextStyle(color: Colors.white70, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (readiness.readinessPercentage / 100.0).clamp(0.0, 1.0),
              backgroundColor: Colors.white24,
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.amber),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            readiness.readinessMessage,
            style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Widget _buildCognitiveDiagnosticCard(BuildContext context, CognitiveDiagnosisModel da) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.purple.withAlpha(15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.purple.withAlpha(50), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.psychology_alt_rounded, color: AppColors.purple, size: 22),
              SizedBox(width: 10),
              Text(
                'COGNITIVE DIAGNOSIS',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                  color: AppColors.purple,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            da.coreIssue,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            da.deepExplanation,
            style: const TextStyle(
              fontSize: 13,
              color: AppColors.lightTextSecondary,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRemediationBanner(BuildContext context, RemediationActionModel remediation) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.rose.withAlpha(15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.rose.withAlpha(50), width: 1.2),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: AppColors.rose.withAlpha(25),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.school_rounded, color: AppColors.rose, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'RECOMMENDED REMEDIATION',
                  style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.rose),
                ),
                const SizedBox(height: 2),
                Text(
                  'Immediate Socratic re-teaching on ${remediation.targetTopic}',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 2),
                const Text(
                  'Step-by-step conceptual walkthrough with the AI Teacher.',
                  style: TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
                ),
              ],
            ),
          ),
          ElevatedButton(
            onPressed: () => _launchSocraticReteach(context, remediation),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.rose,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            child: const Text('Reteach', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildTopicBreakdownSection(BuildContext context, List<TopicPerformanceModel> topics) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: const [
            Text('Topic Performance Breakdown', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text('Target: ≥ 70%', style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary)),
          ],
        ),
        const SizedBox(height: 12),
        ...topics.map((t) => _buildTopicBar(context, t)),
      ],
    );
  }

  Widget _buildTopicBar(BuildContext context, TopicPerformanceModel t) {
    Color tierColor;
    switch (t.tier) {
      case 'Strong':
        tierColor = AppColors.emerald;
        break;
      case 'Good':
        tierColor = AppColors.sky;
        break;
      case 'Weak':
        tierColor = AppColors.amber;
        break;
      default:
        tierColor = AppColors.rose;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
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
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(t.topic, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: tierColor.withAlpha(25),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '${t.tier.toUpperCase()} • ${t.scorePercentage.toInt()}%',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: tierColor),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (t.scorePercentage / 100.0).clamp(0.0, 1.0),
              backgroundColor: Colors.grey.withAlpha(30),
              valueColor: AlwaysStoppedAnimation<Color>(tierColor),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${t.correctCount} of ${t.questionCount} questions correct',
                style: const TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
              ),
              Text(
                '${t.marksObtained.toStringAsFixed(1)} / ${t.totalMarks.toInt()} pts',
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.lightTextSecondary),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildReadinessDimensionsSection(BuildContext context, ExamReadinessDetailModel readiness) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.lightBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.query_stats_rounded, size: 20, color: AppColors.primary),
              SizedBox(width: 8),
              Text('Readiness Engine Projections', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            readiness.actionableProjection,
            style: const TextStyle(fontSize: 13, height: 1.45, fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 14),
          const Divider(),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: readiness.dimensionScores.entries.map((e) {
              final label = e.key.replaceAll('_', ' ').toUpperCase();
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: Colors.grey.withAlpha(20),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '$label: ${e.value.toInt()}%',
                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: AppColors.lightTextSecondary),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  void _launchSocraticReteach(BuildContext context, RemediationActionModel remediation) {
    InteractiveTeacherScreen.open(
      context,
      topic: remediation.targetTopic,
      subject: 'Operating Systems',
    );
  }
}
