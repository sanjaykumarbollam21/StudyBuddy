import 'dart:async';
import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../models/voice_model.dart';
import '../services/voice_api_service.dart';

class VoiceTeacherScreen extends StatefulWidget {
  final String topic;
  final String subject;
  final String? documentId;
  final String? documentName;
  final String? initialPrompt;

  const VoiceTeacherScreen({
    super.key,
    this.topic = 'Deadlocks',
    this.subject = 'Operating Systems',
    this.documentId,
    this.documentName,
    this.initialPrompt,
  });

  static Future<void> open(
    BuildContext context, {
    String topic = 'Deadlocks',
    String? subject,
    String? documentId,
    String? documentName,
    String? initialPrompt,
  }) {
    return Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => VoiceTeacherScreen(
          topic: topic,
          subject: subject ?? 'Operating Systems',
          documentId: documentId,
          documentName: documentName,
          initialPrompt: initialPrompt,
        ),
      ),
    );
  }

  @override
  State<VoiceTeacherScreen> createState() => _VoiceTeacherScreenState();
}

class _VoiceTeacherScreenState extends State<VoiceTeacherScreen> with SingleTickerProviderStateMixin {
  final VoiceApiService _apiService = VoiceApiService();
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  VoiceState _voiceState = VoiceState.idle;
  String? _sessionId;
  late String _currentTopic;

  // Attached image or diagram
  String? _attachedImageFilename;
  String? _attachedImageData;

  // Transcript dialogue
  final List<VoiceDialogueMessage> _messages = [];

  // Quick suggestion chips
  List<String> _quickPrompts = [
    'Explain Deadlocks to me',
    'Quiz me on this',
    'Give me a hint',
    'Make it simpler',
    'Ask me another question',
    'Explain page 42',
  ];

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;
  Timer? _speechTimer;

  @override
  void initState() {
    super.initState();
    _currentTopic = widget.topic;

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1400),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.92, end: 1.10).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Initial greeting or initial prompt
    _initializeDialogue();
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _speechTimer?.cancel();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _initializeDialogue() {
    if (widget.initialPrompt != null && widget.initialPrompt!.isNotEmpty) {
      _handleSpokenInput(widget.initialPrompt!);
    } else {
      // Teacher initial spoken greeting
      final greeting =
          'Hello! I am your AI Teacher sitting right beside you. '
          'We can talk about $_currentTopic, walk through diagrams, or quiz your understanding. What would you like to explore?';

      setState(() {
        _messages.add(
          VoiceDialogueMessage(
            sender: 'teacher',
            text: '### 🎙️ Study Buddy Voice Teacher\n\n$greeting',
            spokenText: greeting,
          ),
        );
      });
      _simulateTeacherSpeaking(greeting);
    }
  }

  void _simulateTeacherSpeaking(String spokenScript) {
    _speechTimer?.cancel();
    setState(() {
      _voiceState = VoiceState.speaking;
    });

    // Simulate natural speech duration based on word count
    final wordCount = spokenScript.split(' ').length;
    final durationSeconds = (wordCount * 0.28).clamp(2.0, 7.0);

    _speechTimer = Timer(Duration(milliseconds: (durationSeconds * 1000).toInt()), () {
      if (mounted && _voiceState == VoiceState.speaking) {
        setState(() {
          _voiceState = VoiceState.idle;
        });
      }
    });
  }

  void _interruptTeacher() {
    _speechTimer?.cancel();
    if (_voiceState == VoiceState.speaking) {
      setState(() {
        _voiceState = VoiceState.interrupted;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Audio paused. Teacher is listening to you.'),
          duration: Duration(seconds: 1),
          backgroundColor: AppColors.primary,
        ),
      );
      Future.delayed(const Duration(milliseconds: 400), () {
        if (mounted) setState(() => _voiceState = VoiceState.idle);
      });
    }
  }

  void _toggleMicrophone() {
    if (_voiceState == VoiceState.speaking) {
      _interruptTeacher();
      return;
    }

    if (_voiceState == VoiceState.listening) {
      setState(() => _voiceState = VoiceState.idle);
    } else {
      setState(() => _voiceState = VoiceState.listening);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Listening to your voice... Speak naturally or tap a quick chip.'),
          duration: Duration(seconds: 2),
          backgroundColor: AppColors.emerald,
        ),
      );
    }
  }

  Future<void> _handleSpokenInput(String utterance) async {
    final text = utterance.trim();
    if (text.isEmpty && _attachedImageData == null && _attachedImageFilename == null) return;

    _speechTimer?.cancel();

    // 1. Add student message to transcript
    setState(() {
      _voiceState = VoiceState.thinking;
      _messages.add(
        VoiceDialogueMessage(
          sender: 'student',
          text: text.isNotEmpty ? text : 'Attached Study Material for Analysis',
          imageSnippet: _attachedImageFilename,
        ),
      );
    });
    _scrollToBottom();

    final sentImageData = _attachedImageData;
    final sentFilename = _attachedImageFilename;

    // Reset attached image in tray
    setState(() {
      _attachedImageData = null;
      _attachedImageFilename = null;
    });

    // 2. Query Voice & Multimodal Service
    final turn = await _apiService.sendVoiceTurn(
      transcript: text,
      sessionId: _sessionId,
      currentTopic: _currentTopic,
      currentSubject: widget.subject,
      imageData: sentImageData,
      imageFilename: sentFilename,
      documentId: widget.documentId,
    );

    if (mounted) {
      setState(() {
        _sessionId = turn.sessionId;
        if (turn.conceptTitle != null) {
          _currentTopic = turn.conceptTitle!;
        }
        if (turn.suggestedQuickActions.isNotEmpty) {
          _quickPrompts = turn.suggestedQuickActions;
        }

        _messages.add(
          VoiceDialogueMessage(
            sender: 'teacher',
            text: turn.teacherReplyText,
            spokenText: turn.spokenText,
          ),
        );
      });
      _scrollToBottom();

      // 3. Trigger teacher speaking simulation
      _simulateTeacherSpeaking(turn.spokenText);
    }
  }

  void _attachMockDiagram(String diagramName) {
    setState(() {
      _attachedImageFilename = diagramName;
      _attachedImageData = 'data:image/png;base64,mockDiagramData';
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Attached "$diagramName" for multimodal teacher analysis.'),
        backgroundColor: AppColors.purple,
        duration: const Duration(seconds: 2),
      ),
    );
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
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.record_voice_over_rounded, size: 18, color: AppColors.primary),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Voice Teacher: $_currentTopic',
                    style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            const Text(
              'Speech • Multimodal Visuals • Document Grounding',
              style: TextStyle(fontSize: 11, color: AppColors.lightTextSecondary),
              overflow: TextOverflow.ellipsis,
            ),
          ],
        ),
        actions: [
          // Audio Mute/Interrupt Toggle
          if (_voiceState == VoiceState.speaking)
            IconButton(
              icon: const Icon(Icons.pause_circle_rounded, color: AppColors.rose),
              tooltip: 'Interrupt Teacher',
              onPressed: _interruptTeacher,
            ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.image_outlined),
            tooltip: 'Attach study visual',
            onSelected: _attachMockDiagram,
            itemBuilder: (ctx) => [
              const PopupMenuItem(
                value: 'Deadlock Wait-For-Graph Diagram.png',
                child: Text('🖼️ Wait-For-Graph Diagram'),
              ),
              const PopupMenuItem(
                value: 'CPU Scheduling Gantt Chart.png',
                child: Text('📊 CPU Gantt Chart Timeline'),
              ),
              const PopupMenuItem(
                value: 'Hierarchical Paging Architecture.png',
                child: Text('📄 Two-Level Paging Diagram'),
              ),
              const PopupMenuItem(
                value: 'Semaphore Mutex Lock Code.png',
                child: Text('💻 POSIX Semaphore Code Snippet'),
              ),
            ],
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            // Voice State & Animated Visualizer Orb HUD
            _buildVoiceVisualizerHud(),

            const Divider(height: 1),

            // Transcript Dialogue Feed
            Expanded(
              child: ListView.builder(
                controller: _scrollController,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                itemCount: _messages.length,
                itemBuilder: (context, idx) {
                  final msg = _messages[idx];
                  return _buildDialogueMessageCard(msg);
                },
              ),
            ),

            // Attached Media Tray
            if (_attachedImageFilename != null)
              _buildAttachedMediaTray(),

            // Quick Spoken Action Chips
            _buildQuickSuggestionChips(),

            // Bottom Audio Control & Input Bar
            _buildBottomControlBar(),
          ],
        ),
      ),
    );
  }

  Widget _buildVoiceVisualizerHud() {
    Color orbColor;
    String statusText;
    IconData stateIcon;

    switch (_voiceState) {
      case VoiceState.listening:
        orbColor = AppColors.emerald;
        statusText = 'LISTENING... SPEAK YOUR QUESTION';
        stateIcon = Icons.mic_rounded;
        break;
      case VoiceState.thinking:
        orbColor = AppColors.purple;
        statusText = 'ANALYZING CONCEPT & MULTIMODAL CONTEXT...';
        stateIcon = Icons.psychology_rounded;
        break;
      case VoiceState.speaking:
        orbColor = AppColors.primary;
        statusText = 'TEACHER SPEAKING (TAP TO INTERRUPT)';
        stateIcon = Icons.volume_up_rounded;
        break;
      case VoiceState.interrupted:
        orbColor = AppColors.rose;
        statusText = 'PAUSED';
        stateIcon = Icons.pause_rounded;
        break;
      case VoiceState.idle:
        orbColor = AppColors.primaryLight;
        statusText = 'VOICE TEACHER READY';
        stateIcon = Icons.graphic_eq_rounded;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
      ),
      child: Row(
        children: [
          // Animated Pulsing Orb
          ScaleTransition(
            scale: _voiceState == VoiceState.speaking || _voiceState == VoiceState.listening
                ? _pulseAnimation
                : const AlwaysStoppedAnimation(1.0),
            child: GestureDetector(
              onTap: _toggleMicrophone,
              child: Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: orbColor,
                  boxShadow: [
                    BoxShadow(
                      color: orbColor.withAlpha(90),
                      blurRadius: 10,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: Icon(stateIcon, color: Colors.white, size: 22),
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  statusText,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                    color: orbColor,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  _voiceState == VoiceState.speaking
                      ? 'Explaining concept with natural voice'
                      : 'Speak naturally, ask for hints, or quiz me',
                  style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                ),
              ],
            ),
          ),
          if (_voiceState == VoiceState.speaking)
            TextButton.icon(
              onPressed: _interruptTeacher,
              icon: const Icon(Icons.stop_circle_rounded, size: 16, color: AppColors.rose),
              label: const Text('Interrupt', style: TextStyle(color: AppColors.rose, fontSize: 12, fontWeight: FontWeight.bold)),
            ),
        ],
      ),
    );
  }

  Widget _buildDialogueMessageCard(VoiceDialogueMessage msg) {
    final isTeacher = msg.sender == 'teacher';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: isTeacher ? MainAxisAlignment.start : MainAxisAlignment.end,
        children: [
          if (isTeacher)
            Container(
              margin: const EdgeInsets.only(right: 10, top: 4),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppColors.primary.withAlpha(20),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.school_rounded, size: 16, color: AppColors.primary),
            ),
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isTeacher
                    ? Theme.of(context).cardTheme.color
                    : AppColors.primary,
                borderRadius: BorderRadius.circular(14),
                border: isTeacher
                    ? Border.all(color: AppColors.lightBorder)
                    : null,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (msg.imageSnippet != null)
                    Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withAlpha(40),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.image_outlined, size: 14, color: Colors.white),
                          const SizedBox(width: 6),
                          Text(msg.imageSnippet!, style: const TextStyle(fontSize: 11, color: Colors.white)),
                        ],
                      ),
                    ),
                  Text(
                    msg.text,
                    style: TextStyle(
                      fontSize: 14,
                      height: 1.45,
                      color: isTeacher ? null : Colors.white,
                    ),
                  ),
                  if (isTeacher && msg.spokenText != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 8),
                      child: Row(
                        children: [
                          InkWell(
                            onTap: () => _simulateTeacherSpeaking(msg.spokenText!),
                            child: Row(
                              children: const [
                                Icon(Icons.replay_circle_filled_rounded, size: 16, color: AppColors.primary),
                                SizedBox(width: 4),
                                Text('Replay Voice', style: TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
          if (!isTeacher)
            Container(
              margin: const EdgeInsets.only(left: 10, top: 4),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppColors.emerald.withAlpha(20),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.person_rounded, size: 16, color: AppColors.emerald),
            ),
        ],
      ),
    );
  }

  Widget _buildAttachedMediaTray() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: AppColors.purple.withAlpha(15),
      child: Row(
        children: [
          const Icon(Icons.image_rounded, size: 18, color: AppColors.purple),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              'Attached for Multimodal Analysis: $_attachedImageFilename',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.purple),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close_rounded, size: 16, color: AppColors.purple),
            onPressed: () => setState(() {
              _attachedImageFilename = null;
              _attachedImageData = null;
            }),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickSuggestionChips() {
    return Container(
      height: 44,
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 14),
        itemCount: _quickPrompts.length,
        itemBuilder: (ctx, idx) {
          final prompt = _quickPrompts[idx];
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ActionChip(
              label: Text(prompt, style: const TextStyle(fontSize: 11)),
              backgroundColor: Theme.of(context).cardTheme.color,
              side: const BorderSide(color: AppColors.lightBorder),
              onPressed: () => _handleSpokenInput(prompt),
            ),
          );
        },
      ),
    );
  }

  Widget _buildBottomControlBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).cardTheme.color,
        border: const Border(top: BorderSide(color: AppColors.lightBorder)),
      ),
      child: Row(
        children: [
          // Microphone Toggle
          IconButton(
            icon: Icon(
              _voiceState == VoiceState.listening ? Icons.mic : Icons.mic_none,
              color: _voiceState == VoiceState.listening ? AppColors.emerald : AppColors.primary,
              size: 26,
            ),
            tooltip: 'Toggle Speech Input',
            onPressed: _toggleMicrophone,
          ),

          // Attachment Action
          IconButton(
            icon: const Icon(Icons.add_photo_alternate_outlined, color: AppColors.lightTextSecondary),
            tooltip: 'Attach Diagram or Note',
            onPressed: () => _attachMockDiagram('Deadlock Wait-For-Graph Diagram.png'),
          ),

          const SizedBox(width: 6),

          // Text Field Fallback
          Expanded(
            child: TextField(
              controller: _textController,
              decoration: InputDecoration(
                hintText: 'Speak or type to your teacher...',
                hintStyle: const TextStyle(fontSize: 13),
                contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                filled: true,
                fillColor: Theme.of(context).brightness == Brightness.dark
                    ? AppColors.darkSurfaceAlt
                    : AppColors.lightSurfaceAlt,
              ),
              onSubmitted: (val) {
                if (val.trim().isNotEmpty) {
                  _handleSpokenInput(val);
                  _textController.clear();
                }
              },
            ),
          ),

          const SizedBox(width: 8),

          // Send Button
          IconButton(
            icon: const Icon(Icons.arrow_upward_rounded, color: AppColors.primary),
            onPressed: () {
              if (_textController.text.trim().isNotEmpty || _attachedImageData != null) {
                _handleSpokenInput(_textController.text);
                _textController.clear();
              }
            },
          ),
        ],
      ),
    );
  }
}
