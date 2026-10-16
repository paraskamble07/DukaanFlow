import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:dukaanflow/core/localization/app_localizations.dart';
import 'package:dukaanflow/core/network/api_client.dart';
import 'package:dukaanflow/core/sync/sync_status_provider.dart';
import 'package:dukaanflow/shared_widgets/sync_status_banner.dart';

/// A notifier we can poke directly, so the widget tests never touch the
/// network or the 15s health-ping timer of the real one. Extending the real
/// notifier keeps `overrideWith`'s type contract; its timer is simply never
/// started in these tests.
class _FakeSyncNotifier extends SyncStatusNotifier {
  _FakeSyncNotifier(SyncStatus initial) : super(ApiClient()) {
    state = initial;
  }
  void emit(SyncStatus status) => state = status;
}

void main() {
  Widget harness(_FakeSyncNotifier notifier) {
    return ProviderScope(
      overrides: [
        syncStatusProvider.overrideWith((ref) => notifier),
      ],
      child: const MaterialApp(
        locale: Locale('en'),
        localizationsDelegates: [
          AppLocalizationsDelegate(),
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
        ],
        supportedLocales: [Locale('en'), Locale('hi'), Locale('mr')],
        home: Scaffold(body: SyncStatusBanner()),
      ),
    );
  }

  testWidgets('offline with queued bills shows the Offline — N bill(s) message',
      (tester) async {
    await tester.pumpWidget(harness(_FakeSyncNotifier(const SyncStatus(
      isOnline: false,
      isSyncing: false,
      pendingCount: 2,
    ))));

    expect(
      find.text('Offline — 2 bill(s) saved locally'),
      findsOneWidget,
      reason: 'The user must be told their bills are safe on the device, '
          'with the exact count',
    );
    expect(find.text('Retry now'), findsOneWidget);
    expect(find.byIcon(Icons.wifi_off_rounded), findsOneWidget);
  });

  testWidgets('offline with nothing queued shows the plain offline bar',
      (tester) async {
    await tester.pumpWidget(harness(_FakeSyncNotifier(const SyncStatus(
      isOnline: false,
      isSyncing: false,
      pendingCount: 0,
    ))));

    expect(find.byIcon(Icons.wifi_off_rounded), findsOneWidget);
    expect(find.textContaining('You are offline'), findsOneWidget);
    // No count may be shown when nothing is queued.
    expect(find.textContaining('bill(s)'), findsNothing);
  });

  testWidgets('online while syncing shows Syncing N bill(s)… and no retry action',
      (tester) async {
    await tester.pumpWidget(harness(_FakeSyncNotifier(const SyncStatus(
      isOnline: true,
      isSyncing: true,
      pendingCount: 3,
    ))));

    expect(find.text('Syncing 3 bill(s)…'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    // "Retry now" belongs to the offline state only.
    expect(find.text('Retry now'), findsNothing);
    expect(find.byIcon(Icons.wifi_off_rounded), findsNothing);
  });

  testWidgets('online and fully synced renders nothing', (tester) async {
    await tester.pumpWidget(harness(_FakeSyncNotifier(const SyncStatus(
      isOnline: true,
      isSyncing: false,
      pendingCount: 0,
    ))));

    expect(find.byType(SyncStatusBanner), findsOneWidget);
    final banner = tester.getSize(find.byType(SyncStatusBanner));
    expect(banner.height, 0.0, reason: 'A healthy status must not occupy space');
    expect(find.byIcon(Icons.wifi_off_rounded), findsNothing);
    expect(find.byType(CircularProgressIndicator), findsNothing);
  });

  testWidgets('the banner reflects later state changes', (tester) async {
    final notifier = _FakeSyncNotifier(const SyncStatus(
      isOnline: false,
      isSyncing: false,
      pendingCount: 1,
    ));
    await tester.pumpWidget(harness(notifier));
    expect(find.text('Offline — 1 bill(s) saved locally'), findsOneWidget);

    // ... connectivity returns and the queue drains:
    notifier.emit(const SyncStatus(
      isOnline: true,
      isSyncing: true,
      pendingCount: 1,
    ));
    await tester.pump();
    expect(find.text('Syncing 1 bill(s)…'), findsOneWidget);

    notifier.emit(const SyncStatus(
      isOnline: true,
      isSyncing: false,
      pendingCount: 0,
    ));
    await tester.pump();
    expect(find.byIcon(Icons.wifi_off_rounded), findsNothing);
    expect(find.textContaining('Syncing'), findsNothing);
  });

  group('SyncStatus', () {
    test('hasPending is derived from pendingCount', () {
      const empty = SyncStatus(
          isOnline: true, isSyncing: false, pendingCount: 0, lastSyncedAt: null);
      const queued = SyncStatus(
          isOnline: false, isSyncing: false, pendingCount: 4, lastSyncedAt: null);
      expect(empty.hasPending, isFalse);
      expect(queued.hasPending, isTrue);
    });

    test('copyWith leaves unmentioned fields untouched', () {
      final now = DateTime(2026, 10, 16);
      final original = SyncStatus(
          isOnline: true, isSyncing: true, pendingCount: 2, lastSyncedAt: now);
      final updated = original.copyWith(isSyncing: false, pendingCount: 0);

      expect(updated.isOnline, isTrue);
      expect(updated.isSyncing, isFalse);
      expect(updated.pendingCount, 0);
      expect(updated.lastSyncedAt, now);
      expect(updated.hasPending, isFalse);
    });
  });
}
