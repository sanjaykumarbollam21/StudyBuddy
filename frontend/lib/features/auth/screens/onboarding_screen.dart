import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../shared/widgets/app_button.dart';
import '../../../shared/widgets/app_text_field.dart';
import '../controllers/auth_controller.dart';
import '../models/user_model.dart';
import '../../dashboard/screens/main_shell_screen.dart';

class OnboardingScreen extends StatefulWidget {
  final AuthController authController;

  const OnboardingScreen({super.key, required this.authController});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  String _educationLevel = 'Undergraduate';
  final _goalController = TextEditingController(text: 'Prepare for Semester Exams & Master Concepts');
  int _dailyAvailableMins = 120;
  final int _preferredDurationMins = 45;
  String _learningStyle = 'visual_practical';
  final String _knowledgeLevel = 'intermediate';

  final List<String> _educationLevels = [
    'High School',
    'Undergraduate',
    'Graduate / Masters',
    'Self-Learner / Professional',
  ];

  final Map<String, String> _learningStyles = {
    'visual_practical': 'Visual & Practical (Examples first)',
    'conceptual': 'Conceptual & Deep Dive (Theory first)',
    'practice_first': 'Practice First (Quizzes & Exercises)',
  };

  @override
  void dispose() {
    _goalController.dispose();
    super.dispose();
  }

  void _finishOnboarding({bool skipped = false}) async {
    final profile = UserProfile(
      educationLevel: skipped ? 'Self-Learner' : _educationLevel,
      targetGoals: skipped ? 'General Mastery' : _goalController.text.trim(),
      dailyAvailableMins: _dailyAvailableMins,
      preferredStudyDurationMins: _preferredDurationMins,
      learningStyle: _learningStyle,
      currentKnowledgeLevel: _knowledgeLevel,
    );

    await widget.authController.updateProfile(profile);

    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => MainShellScreen(authController: widget.authController),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Personalize Study Buddy'),
        actions: [
          TextButton(
            onPressed: () => _finishOnboarding(skipped: true),
            child: const Text('Skip for now'),
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 520),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Tell Study Buddy About Yourself 🎓',
                    style: Theme.of(context).textTheme.headlineMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Your answers help your AI teacher adapt explanations and pace.',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 28),

                  // Education Level Selection
                  const Text('Education Level', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _educationLevels.map((lvl) {
                      final isSelected = _educationLevel == lvl;
                      return ChoiceChip(
                        label: Text(lvl),
                        selected: isSelected,
                        selectedColor: AppColors.primary.withAlpha(40),
                        onSelected: (val) {
                          if (val) setState(() => _educationLevel = lvl);
                        },
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 22),

                  // Learning Goal
                  AppTextField(
                    controller: _goalController,
                    label: 'Primary Learning Goal',
                    hint: 'e.g. Master Operating Systems & Python',
                    prefixIcon: Icons.flag_outlined,
                  ),
                  const SizedBox(height: 22),

                  // Preferred Learning Style
                  const Text('Preferred Learning Style', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  Column(
                    children: _learningStyles.entries.map((entry) {
                      final isSelected = _learningStyle == entry.key;
                      return InkWell(
                        onTap: () => setState(() => _learningStyle = entry.key),
                        borderRadius: BorderRadius.circular(10),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          margin: const EdgeInsets.only(bottom: 6),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10),
                            color: isSelected ? AppColors.primary.withAlpha(25) : Colors.transparent,
                            border: Border.all(
                              color: isSelected ? AppColors.primary : AppColors.lightBorder,
                            ),
                          ),
                          child: Row(
                            children: [
                              Icon(
                                isSelected ? Icons.radio_button_checked : Icons.radio_button_off,
                                size: 20,
                                color: isSelected ? AppColors.primary : Colors.grey,
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Text(
                                  entry.value,
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 18),

                  // Daily Study Budget Slider
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('Daily Available Study Time', style: TextStyle(fontWeight: FontWeight.w600)),
                      Text(
                        '${(_dailyAvailableMins / 60).toStringAsFixed(1)} hours/day',
                        style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary),
                      ),
                    ],
                  ),
                  Slider(
                    value: _dailyAvailableMins.toDouble(),
                    min: 30,
                    max: 360,
                    divisions: 11,
                    activeColor: AppColors.primary,
                    onChanged: (val) {
                      setState(() => _dailyAvailableMins = val.round());
                    },
                  ),
                  const SizedBox(height: 28),

                  // Submit Button
                  ListenableBuilder(
                    listenable: widget.authController,
                    builder: (context, _) {
                      return AppButton(
                        text: 'Save & Start Learning',
                        isLoading: widget.authController.isLoading,
                        onPressed: () => _finishOnboarding(skipped: false),
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
