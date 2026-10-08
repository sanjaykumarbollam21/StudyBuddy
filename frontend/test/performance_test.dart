import 'package:flutter_test/flutter_test.dart';
import 'package:frontend/core/performance/performance_monitor.dart';
import 'package:frontend/core/storage/android_local_llm_provider.dart';

void main() {
  group('Phase 15+ Performance Test Suite', () {
    test('PerformanceMonitor records and computes rolling statistics correctly', () {
      final monitor = PerformanceMonitor();

      monitor.record('db_query', 12.0);
      monitor.record('db_query', 18.0);
      monitor.record('db_query', 15.0);

      final summary = monitor.getSummary();
      expect(summary.containsKey('db_query'), isTrue);

      final dbStats = summary['db_query'] as Map<String, dynamic>;
      expect(dbStats['count'], equals(3));
      expect(dbStats['p50_ms'], equals(15.0));
      expect(dbStats['max_ms'], equals(18.0));
    });

    test('PerformanceMonitor trace synchronous blocks correctly', () {
      final res = PerformanceMonitor.trace('sync_computation', () {
        int sum = 0;
        for (int i = 0; i < 1000; i++) {
          sum += i;
        }
        return sum;
      });

      expect(res, equals(499500));
      final summary = PerformanceMonitor().getSummary();
      expect(summary.containsKey('sync_computation'), isTrue);
    });

    test('AndroidLocalLLMProvider maintains singleton and lifecycle state transitions', () async {
      final provider1 = AndroidLocalLLMProvider();
      final provider2 = AndroidLocalLLMProvider();

      expect(identical(provider1, provider2), isTrue, reason: 'Must return identical singleton instance');

      await provider1.ensureModelLoaded();
      expect(
        provider1.lifecycleState == ModelLifecycleState.ready ||
            provider1.lifecycleState == ModelLifecycleState.idle,
        isTrue,
      );
    });

    test('AndroidLocalLLMProvider streams tokens progressively', () async {
      final provider = AndroidLocalLLMProvider();
      final tokens = <String>[];

      await for (final token in provider.streamSocraticResponse(
        prompt: 'What causes deadlocks?',
        conceptTitle: 'Deadlocks',
      )) {
        tokens.add(token);
      }

      expect(tokens.isNotEmpty, isTrue);
      final fullResponse = tokens.join('');
      expect(fullResponse.contains('Coffman') || fullResponse.contains('deadlock') || fullResponse.contains('Person'), isTrue);
    });
  });
}
