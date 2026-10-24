import 'dart:developer' as developer;
import 'package:flutter/foundation.dart';

class PerformanceRecord {
  final String operation;
  final double durationMs;
  final bool success;
  final DateTime timestamp;
  final Map<String, dynamic>? metadata;

  PerformanceRecord({
    required this.operation,
    required this.durationMs,
    required this.success,
    required this.timestamp,
    this.metadata,
  });
}

class PerformanceMonitor {
  static final PerformanceMonitor _instance = PerformanceMonitor._internal();
  factory PerformanceMonitor() => _instance;
  PerformanceMonitor._internal();

  final Map<String, List<double>> _durations = {};
  final Map<String, int> _counts = {};
  final Map<String, int> _errorCounts = {};
  static const int _maxHistory = 200;

  /// Trace a synchronous function execution
  static T trace<T>(String operation, T Function() block, {Map<String, dynamic>? metadata}) {
    final sw = Stopwatch()..start();
    bool success = true;
    try {
      return block();
    } catch (e) {
      success = false;
      rethrow;
    } finally {
      sw.stop();
      final ms = sw.elapsedMicroseconds / 1000.0;
      _instance.record(operation, ms, success: success, metadata: metadata);
    }
  }

  /// Trace an asynchronous function execution
  static Future<T> traceAsync<T>(String operation, Future<T> Function() block, {Map<String, dynamic>? metadata}) async {
    final sw = Stopwatch()..start();
    bool success = true;
    try {
      return await block();
    } catch (e) {
      success = false;
      rethrow;
    } finally {
      sw.stop();
      final ms = sw.elapsedMicroseconds / 1000.0;
      _instance.record(operation, ms, success: success, metadata: metadata);
    }
  }

  void record(String operation, double durationMs, {bool success = true, Map<String, dynamic>? metadata}) {
    _durations.putIfAbsent(operation, () => []);
    _counts[operation] = (_counts[operation] ?? 0) + 1;
    if (!success) {
      _errorCounts[operation] = (_errorCounts[operation] ?? 0) + 1;
    }

    final list = _durations[operation]!;
    list.add(durationMs);
    if (list.length > _maxHistory) {
      list.removeAt(0);
    }

    // Standardized log output
    String metaStr = '';
    if (metadata != null && metadata.isNotEmpty) {
      final sanitized = Map<String, dynamic>.from(metadata)
        ..removeWhere((k, _) => k.contains('token') || k.contains('pass') || k.contains('text') || k.contains('answer'));
      if (sanitized.isNotEmpty) {
        metaStr = ' ${sanitized.entries.map((e) => '${e.key}=${e.value}').join(' ')}';
      }
    }

    if (kDebugMode) {
      developer.log(
        'PERF operation=$operation duration_ms=${durationMs.toStringAsFixed(1)} success=$success$metaStr',
        name: 'PerformanceMonitor',
      );
    }
  }

  Map<String, dynamic> getSummary() {
    final summary = <String, dynamic>{};
    for (final entry in _durations.entries) {
      final op = entry.key;
      final vals = entry.value;
      if (vals.isEmpty) continue;
      final sorted = List<double>.from(vals)..sort();
      final n = sorted.length;
      final p50 = sorted[(n * 0.5).toInt()];
      final p95 = sorted[(n * 0.95).toInt().clamp(0, n - 1)];
      final avg = vals.reduce((a, b) => a + b) / n;

      summary[op] = {
        'count': _counts[op] ?? 0,
        'errors': _errorCounts[op] ?? 0,
        'avg_ms': double.parse(avg.toStringAsFixed(1)),
        'min_ms': double.parse(sorted.first.toStringAsFixed(1)),
        'max_ms': double.parse(sorted.last.toStringAsFixed(1)),
        'p50_ms': double.parse(p50.toStringAsFixed(1)),
        'p95_ms': double.parse(p95.toStringAsFixed(1)),
      };
    }
    return summary;
  }

  double getAverage(String operation) {
    final list = _durations[operation];
    if (list == null || list.isEmpty) return 0.0;
    return list.reduce((a, b) => a + b) / list.length;
  }

  void clear() {
    _durations.clear;
    _counts.clear();
    _errorCounts.clear();
  }
}
