import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/ads/ads_service.dart';
import 'core/ads/consent_service.dart';
import 'core/constants/app_colors.dart';
import 'core/localization/app_localizations.dart';
import 'core/sync/sync_status_provider.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/splash_screen.dart';
import 'features/settings/app_update_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/pos/pos_screen.dart';
import 'features/inventory/product_list_screen.dart';
import 'features/customers/customer_list_screen.dart';
import 'features/more/more_screen.dart';
import 'features/sales/sales_history_screen.dart';
import 'providers/settings_provider.dart';
import 'providers/update_provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  // Phase 12: Google UMP consent + AdMob SDK. Runs concurrently with the
  // splash screen and never blocks the app: if consent or the SDK is
  // unavailable, banners simply stay hidden.
  _initAds();
  runApp(const ProviderScope(child: ShopZenApp()));
}

/// Requests UMP consent (showing the form when required) and initializes the
/// AdMob SDK only when consent permits ad requests.
Future<void> _initAds() async {
  try {
    final result = await ConsentService.instance.requestConsent();
    await AdsService.instance.initialize(consentGranted: result.canRequestAds);
  } catch (_) {
    // Ads are optional; any unexpected failure leaves banners disabled.
  }
}

class ShopZenApp extends ConsumerWidget {
  const ShopZenApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final settings = ref.watch(settingsProvider);
    return MaterialApp(
      title: 'ShopZen',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: settings.themeMode,
      locale: settings.locale,
      supportedLocales: const [
        Locale('en'),
        Locale('hi'),
        Locale('mr'),
      ],
      localizationsDelegates: const [
        AppLocalizationsDelegate(),
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ],
      home: const SplashScreen(),
    );
  }
}

/// Central bottom-navigation scaffold: HOME / SALES / STOCK / CUSTOMERS / MORE
/// with + NEW SALE as the primary floating action.
class MainNavigationScaffold extends ConsumerStatefulWidget {
  const MainNavigationScaffold({super.key});

  @override
  ConsumerState<MainNavigationScaffold> createState() => _MainNavigationScaffoldState();
}

class _MainNavigationScaffoldState extends ConsumerState<MainNavigationScaffold> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    DashboardScreen(),
    SalesHistoryScreen(),
    ProductListScreen(),
    CustomerListScreen(),
    MoreScreen(),
  ];

  @override
  void initState() {
    super.initState();
    // User is authenticated when this scaffold mounts — start the
    // connectivity / pending-sync monitor (it also drives the
    // queued-bill upload).
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(syncStatusProvider.notifier).start();
      _checkForMandatoryUpdate();
    });
  }

  /// Silent update check on startup. A non-mandatory newer build is
  /// surfaced later from Settings; a mandatory one blocks the session
  /// because builds below the server's minimum are unsupported.
  Future<void> _checkForMandatoryUpdate() async {
    try {
      final info = await ref.read(appUpdateProvider.notifier).checkForUpdates();
      if (info != null && info.mandatoryUpdate && mounted) {
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (ctx) => PopScope(
            canPop: false,
            child: AlertDialog(
              title: const Text('Update required'),
              content: Text(
                'ShopZen v${info.latestVersion} is available and your current '
                'build (v${info.minimumSupportedVersion} minimum) is no longer '
                'supported. Please update to continue using your shop data safely.',
              ),
              actions: [
                FilledButton(
                  onPressed: () {
                    Navigator.of(ctx).pop();
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const AppUpdateScreen()),
                    );
                  },
                  child: const Text('Update now'),
                ),
              ],
            ),
          ),
        );
      }
    } catch (_) {
      // Update checks must never block the app — offline is fine.
    }
  }

  @override
  void dispose() {
    // Stop pinging / syncing while the user is logged out.
    ref.read(syncStatusProvider.notifier).stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const PosScreen()),
        ),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.point_of_sale_rounded),
        label: Text(l10n.translate('new_sale'),
            style: const TextStyle(fontWeight: FontWeight.bold)),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          indicatorColor: AppColors.primary.withValues(alpha: 0.12),
        ),
        child: NavigationBar(
          selectedIndex: _currentIndex,
          onDestinationSelected: (i) {
            setState(() => _currentIndex = i);
          },
          height: 68,
          destinations: [
            NavigationDestination(
              icon: _navIcon(Icons.home_outlined, Icons.home_rounded, 0),
              label: l10n.translate('dashboard'),
            ),
            NavigationDestination(
              icon: _navIcon(Icons.receipt_long_outlined, Icons.receipt_long_rounded, 1),
              label: l10n.translate('pos_billing'),
            ),
            NavigationDestination(
              icon: _navIcon(Icons.inventory_2_outlined, Icons.inventory_2_rounded, 2),
              label: l10n.translate('inventory'),
            ),
            NavigationDestination(
              icon: _navIcon(Icons.people_outline_rounded, Icons.people_rounded, 3),
              label: l10n.translate('khata'),
            ),
            NavigationDestination(
              icon: _navIcon(Icons.grid_view_outlined, Icons.grid_view_rounded, 4),
              label: l10n.translate('more'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _navIcon(IconData outline, IconData filled, int index) {
    return Icon(
      _currentIndex == index ? filled : outline,
      color: _currentIndex == index ? AppColors.primary : AppColors.textSecondary,
    );
  }
}
