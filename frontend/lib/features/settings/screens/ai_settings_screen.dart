import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/sync/sync_service.dart';

class AISettingsScreen extends StatefulWidget {
  const AISettingsScreen({super.key});

  @override
  State<AISettingsScreen> createState() => _AISettingsScreenState();
}

class _AISettingsScreenState extends State<AISettingsScreen> {
  String _selectedMode = 'offline'; // offline, hybrid, online
  bool _cloudFallback = false;
  String _ollamaModel = 'llama3.2:3b';

  final Map<String, Map<String, dynamic>> _modes = {
    'offline': {
      'title': 'Offline AI',
      'badge': '🟢 Offline AI — No Internet required',
      'color': AppColors.emerald,
      'description':
          'All models, embeddings (BAAI/bge-small-en-v1.5), and pedagogical Socratic logic run directly on your device. Zero external data transmission.',
      'icon': Icons.offline_bolt_rounded,
    },
    'hybrid': {
      'title': 'Hybrid AI',
      'badge': '🟡 Hybrid — Local data + cloud reasoning',
      'color': AppColors.amber,
      'description':
          'Local knowledge indexing and embeddings on device, with cloud reasoning for complex multi-step conceptual explanations.',
      'icon': Icons.cloud_sync_rounded,
    },
    'online': {
      'title': 'Online AI',
      'badge': '🔵 Online — Cloud AI enabled',
      'color': AppColors.primary,
      'description':
          'Full cloud AI acceleration with highest-tier LLM reasoning for in-depth Socratic conversations and exam question generation.',
      'icon': Icons.cloud_done_rounded,
    },
  };

  Future<void> _triggerManualSync() async {
    final syncService = SyncService();
    final messenger = ScaffoldMessenger.of(context);
    final success = await syncService.synchronize();
    if (mounted) {
      messenger.clearSnackBars();
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            success ? 'Sync completed successfully! All changes persisted.' : 'Sync failed or device is offline.',
          ),
          backgroundColor: success ? AppColors.emerald : AppColors.rose,
        ),
      );
    }
  }

  void _saveSettings() {
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('AI Mode switched to ${_modes[_selectedMode]?['title'] ?? _selectedMode}'),
        backgroundColor: AppColors.primary,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final syncService = SyncService();

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Mode & Offline Sync', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      body: ListenableBuilder(
        listenable: syncService,
        builder: (context, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 700),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Mode Indicator Banner
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                      decoration: BoxDecoration(
                        color: (_modes[_selectedMode]?['color'] as Color).withAlpha(20),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: (_modes[_selectedMode]?['color'] as Color).withAlpha(100),
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            _modes[_selectedMode]?['icon'] as IconData,
                            color: _modes[_selectedMode]?['color'] as Color,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              _modes[_selectedMode]?['badge'] as String,
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: _modes[_selectedMode]?['color'] as Color,
                                fontSize: 13,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

                    // AI Mode Options
                    const Text('Select AI Provider Mode', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    ..._modes.entries.map((entry) {
                      final modeKey = entry.key;
                      final info = entry.value;
                      final isSelected = _selectedMode == modeKey;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                          side: BorderSide(
                            color: isSelected ? info['color'] as Color : Colors.transparent,
                            width: 2,
                          ),
                        ),
                        child: InkWell(
                          onTap: () {
                            setState(() => _selectedMode = modeKey);
                            _saveSettings();
                          },
                          borderRadius: BorderRadius.circular(12),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  margin: const EdgeInsets.only(top: 2),
                                  width: 22,
                                  height: 22,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: isSelected ? info['color'] as Color : Colors.grey.shade400,
                                      width: 2,
                                    ),
                                  ),
                                  child: isSelected
                                      ? Center(
                                          child: Container(
                                            width: 12,
                                            height: 12,
                                            decoration: BoxDecoration(
                                              shape: BoxShape.circle,
                                              color: info['color'] as Color,
                                            ),
                                          ),
                                        )
                                      : null,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        info['title'] as String,
                                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        info['description'] as String,
                                        style: const TextStyle(fontSize: 13, color: AppColors.lightTextSecondary),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }),

                    const SizedBox(height: 24),

                    // Local Model Configuration Card
                    const Text('Local Model & Offline Engine', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    Card(
                      child: Column(
                        children: [
                          ListTile(
                            leading: const Icon(Icons.memory_rounded, color: AppColors.primary),
                            title: const Text('Local Embedding Model'),
                            subtitle: const Text('BAAI/bge-small-en-v1.5 (384 dims, ONNX)'),
                            trailing: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.emerald.withAlpha(25),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: const Text('Active', style: TextStyle(color: AppColors.emerald, fontSize: 11, fontWeight: FontWeight.bold)),
                            ),
                          ),
                          const Divider(height: 1),
                          ListTile(
                            leading: const Icon(Icons.psychology_rounded, color: AppColors.primary),
                            title: const Text('Offline Local LLM (Ollama)'),
                            subtitle: Text('Model: $_ollamaModel • 16GB RAM Profile (2048 ctx)'),
                            trailing: DropdownButton<String>(
                              value: _ollamaModel,
                              underline: const SizedBox(),
                              items: const [
                                DropdownMenuItem(value: 'llama3.2:3b', child: Text('Llama 3.2 (3B)')),
                                DropdownMenuItem(value: 'phi3:mini', child: Text('Phi-3 (3.8B)')),
                                DropdownMenuItem(value: 'mistral:7b', child: Text('Mistral (7B)')),
                              ],
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() => _ollamaModel = val);
                                  _saveSettings();
                                }
                              },
                            ),
                          ),
                          const Divider(height: 1),
                          SwitchListTile(
                            secondary: const Icon(Icons.backup_rounded, color: AppColors.primary),
                            title: const Text('Cloud Fallback on Low Memory'),
                            subtitle: const Text('Permit cloud delegation if device resources are low'),
                            value: _cloudFallback,
                            onChanged: (val) {
                              setState(() => _cloudFallback = val);
                              _saveSettings();
                            },
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // Offline-First Sync Section
                    const Text('Offline-First Synchronization', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  backgroundColor: AppColors.primary.withAlpha(25),
                                  child: const Icon(Icons.sync_rounded, color: AppColors.primary),
                                ),
                                const SizedBox(width: 14),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      const Text('Offline Change Queue', style: TextStyle(fontWeight: FontWeight.bold)),
                                      Text(
                                        syncService.pendingCount == 0
                                            ? 'All changes synchronized'
                                            : '${syncService.pendingCount} pending offline changes',
                                        style: const TextStyle(fontSize: 12, color: AppColors.lightTextSecondary),
                                      ),
                                    ],
                                  ),
                                ),
                                ElevatedButton.icon(
                                  onPressed: syncService.isSyncing ? null : _triggerManualSync,
                                  icon: syncService.isSyncing
                                      ? const SizedBox(
                                          width: 14,
                                          height: 14,
                                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                        )
                                      : const Icon(Icons.refresh_rounded, size: 16),
                                  label: Text(syncService.isSyncing ? 'Syncing...' : 'Sync Now'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.primary,
                                    foregroundColor: Colors.white,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Wrap(
                              alignment: WrapAlignment.spaceBetween,
                              runSpacing: 4,
                              children: [
                                const Text('Last Synced Watermark: ', style: TextStyle(fontSize: 12, color: AppColors.lightTextSecondary)),
                                Text(
                                  syncService.lastSyncedAt != null
                                      ? '${syncService.lastSyncedAt!.hour.toString().padLeft(2, '0')}:${syncService.lastSyncedAt!.minute.toString().padLeft(2, '0')}'
                                      : 'Never',
                                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
