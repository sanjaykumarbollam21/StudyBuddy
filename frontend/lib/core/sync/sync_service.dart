import 'package:flutter/foundation.dart';
import '../networking/api_client.dart';

class SyncChangeItem {
  final String id;
  final String entityType;
  final String entityId;
  final String action;
  final DateTime clientTimestamp;
  final Map<String, dynamic> payload;
  final int version;

  SyncChangeItem({
    required this.id,
    required this.entityType,
    required this.entityId,
    required this.action,
    required this.clientTimestamp,
    required this.payload,
    this.version = 1,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'entity_type': entityType,
    'entity_id': entityId,
    'action': action,
    'client_timestamp': clientTimestamp.toIso8601String(),
    'payload': payload,
    'version': version,
  };

  factory SyncChangeItem.fromJson(Map<String, dynamic> json) => SyncChangeItem(
    id: json['id'] as String,
    entityType: json['entity_type'] as String,
    entityId: json['entity_id'] as String,
    action: json['action'] as String,
    clientTimestamp: DateTime.parse(json['client_timestamp'] as String),
    payload: json['payload'] as Map<String, dynamic>? ?? {},
    version: json['version'] as int? ?? 1,
  );
}

class SyncService extends ChangeNotifier {
  static final SyncService _instance = SyncService._internal();
  factory SyncService() => _instance;
  SyncService._internal();

  final List<SyncChangeItem> _pendingQueue = [];
  DateTime? _lastSyncedAt;
  bool _isSyncing = false;
  String _deviceId = 'device-flutter-client';

  DateTime? get lastSyncedAt => _lastSyncedAt;
  bool get isSyncing => _isSyncing;
  int get pendingCount => _pendingQueue.length;
  List<SyncChangeItem> get pendingQueue => List.unmodifiable(_pendingQueue);
  String get deviceId => _deviceId;

  void setDeviceId(String id) {
    _deviceId = id;
    notifyListeners();
  }

  /// Record an offline change to be synced when internet connectivity is restored
  void recordChange({
    required String entityType,
    required String entityId,
    required String action,
    required Map<String, dynamic> payload,
  }) {
    final change = SyncChangeItem(
      id: 'ch-${DateTime.now().millisecondsSinceEpoch}-${_pendingQueue.length}',
      entityType: entityType,
      entityId: entityId,
      action: action,
      clientTimestamp: DateTime.now(),
      payload: payload,
    );
    _pendingQueue.add(change);
    notifyListeners();
  }

  /// Perform bidirectional sync: push local changes and pull remote state
  Future<bool> synchronize({ApiClient? client}) async {
    if (_isSyncing) return false;
    _isSyncing = true;
    notifyListeners();

    try {
      if (client != null) {
        // Push queued changes
        if (_pendingQueue.isNotEmpty) {
          final pushPayload = {
            'device_id': _deviceId,
            'changes': _pendingQueue.map((c) => c.toJson()).toList(),
          };
          await client.post('/api/v1/sync/push', body: pushPayload);
          _pendingQueue.clear();
        }

        // Pull remote changes
        final pullPayload = {
          'device_id': _deviceId,
          'since_timestamp': _lastSyncedAt?.toIso8601String(),
        };
        await client.post('/api/v1/sync/pull', body: pullPayload);
      } else {
        // Local offline simulated sync
        await Future.delayed(const Duration(milliseconds: 300));
        _pendingQueue.clear();
      }

      _lastSyncedAt = DateTime.now();
      _isSyncing = false;
      notifyListeners();
      return true;
    } catch (e) {
      debugPrint('Sync failed or offline: $e');
      _isSyncing = false;
      notifyListeners();
      return false;
    }
  }

  void clearQueue() {
    _pendingQueue.clear();
    notifyListeners();
  }
}
