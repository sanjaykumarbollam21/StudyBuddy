import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../features/agent/models/agent_task_model.dart';

/// Phase 14: Local Offline Storage Engine for Android & Desktop.
/// Caches documents, chunks, mastery, spaced revisions, planner schedule,
/// and persistent AgentTasks so the app functions 100% offline.
class OfflineStorageService {
  static final OfflineStorageService _instance = OfflineStorageService._internal();
  factory OfflineStorageService() => _instance;
  OfflineStorageService._internal();

  static const _keyActiveTask = 'offline_active_agent_task';
  static const _keyMasteryMap = 'offline_mastery_map';
  static const _keyRevisionItems = 'offline_revision_items';
  static const _keyPlannerSchedule = 'offline_planner_schedule';
  static const _keyDocChunksPrefix = 'offline_chunks_';
  static const _keyUserDocuments = 'offline_user_documents';

  String? _activeUserId;
  String? get activeUserId => _activeUserId;
  void setActiveUserId(String? id) {
    _activeUserId = id;
  }

  String _userKey(String baseKey) => _activeUserId != null ? '${_activeUserId}_$baseKey' : baseKey;

  // 1. AgentTask Persistence
  Future<void> saveActiveAgentTask(AgentTaskModel task) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonStr = jsonEncode(task.toJson());
      await prefs.setString(_userKey(_keyActiveTask), jsonStr);
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save active task: $e');
    }
  }

  Future<AgentTaskModel?> loadActiveAgentTask() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey(_keyActiveTask));
      if (raw != null && raw.isNotEmpty) {
        final decoded = jsonDecode(raw) as Map<String, dynamic>;
        return AgentTaskModel.fromJson(decoded);
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load active task: $e');
    }
    return null;
  }

  Future<void> clearActiveAgentTask() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userKey(_keyActiveTask));
  }

  // 2. Mastery Persistence
  Future<void> saveMastery(String topic, double percentage) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final key = _userKey(_keyMasteryMap);
      final raw = prefs.getString(key);
      final map = raw != null ? (jsonDecode(raw) as Map<String, dynamic>) : <String, dynamic>{};
      map[topic.toLowerCase()] = percentage;
      await prefs.setString(key, jsonEncode(map));
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save mastery: $e');
    }
  }

  Future<double?> loadMastery(String topic) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey(_keyMasteryMap));
      if (raw != null) {
        final map = jsonDecode(raw) as Map<String, dynamic>;
        final val = map[topic.toLowerCase()];
        if (val != null) return (val as num).toDouble();
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load mastery: $e');
    }
    return null;
  }

  Future<Map<String, double>> loadAllMastery() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey(_keyMasteryMap));
      if (raw != null) {
        final map = jsonDecode(raw) as Map<String, dynamic>;
        return map.map((k, v) => MapEntry(k, (v as num).toDouble()));
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load all mastery: $e');
    }
    return {};
  }

  // 3. User Documents Persistence
  Future<void> saveUserDocuments(List<Map<String, dynamic>> docs) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey(_keyUserDocuments), jsonEncode(docs));
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save user documents: $e');
    }
  }

  Future<List<Map<String, dynamic>>> loadUserDocuments() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey(_keyUserDocuments));
      if (raw != null) {
        final list = jsonDecode(raw) as List<dynamic>;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load user documents: $e');
    }
    return [];
  }

  // 4. Spaced Revision Persistence
  Future<void> saveRevisionItems(List<Map<String, dynamic>> items) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey(_keyRevisionItems), jsonEncode(items));
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save revision items: $e');
    }
  }

  Future<List<Map<String, dynamic>>> loadRevisionItems() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey(_keyRevisionItems));
      if (raw != null) {
        final list = jsonDecode(raw) as List<dynamic>;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load revision items: $e');
    }
    return [];
  }

  // 5. Document Chunks Persistence
  Future<void> saveDocumentChunks(String docId, List<Map<String, dynamic>> chunks) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey('$_keyDocChunksPrefix$docId'), jsonEncode(chunks));
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save doc chunks: $e');
    }
  }

  Future<List<Map<String, dynamic>>> loadDocumentChunks(String docId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey('$_keyDocChunksPrefix$docId'));
      if (raw != null) {
        final list = jsonDecode(raw) as List<dynamic>;
        return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load doc chunks: $e');
    }
    return [];
  }

  // 6. Planner Schedule Persistence
  Future<void> savePlannerSchedule(Map<String, dynamic> schedule) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_userKey(_keyPlannerSchedule), jsonEncode(schedule));
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save planner schedule: $e');
    }
  }

  Future<Map<String, dynamic>?> loadPlannerSchedule() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_userKey(_keyPlannerSchedule));
      if (raw != null) {
        return jsonDecode(raw) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load planner schedule: $e');
    }
    return null;
  }

  Future<void> clearAllCurrentUserData() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_userKey(_keyMasteryMap));
      await prefs.remove(_userKey(_keyRevisionItems));
      await prefs.remove(_userKey(_keyUserDocuments));
      await prefs.remove(_userKey(_keyPlannerSchedule));
      await prefs.remove(_userKey(_keyActiveTask));
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to clear all current user data: $e');
    }
  }

  // 6. Release & Physical Device Validation Status
  static const _keyPhysicalDeviceVerified = 'offline_physical_device_verified';

  Future<void> savePhysicalDeviceVerified(bool verified) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_keyPhysicalDeviceVerified, verified);
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to save physical device verification: $e');
    }
  }

  Future<bool> isPhysicalDeviceVerified() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_keyPhysicalDeviceVerified) ?? false;
    } catch (e) {
      debugPrint('[OfflineStorage] Failed to load physical device verification: $e');
    }
    return false;
  }
}
