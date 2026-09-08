import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/constants/app_colors.dart';
import 'core/localization/app_localizations.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/splash_screen.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/pos/pos_screen.dart';
import 'features/inventory/product_list_screen.dart';
import 'features/customers/customer_list_screen.dart';
import 'features/more/more_screen.dart';
import 'features/sales/sales_history_screen.dart';
import 'providers/auth_provider.dart';
import 'providers/settings_provider.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );
  runApp(const ProviderScope(child: ShopZenApp()));
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
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: _screens),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const PosScreen()),
        ),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.point_of_sale_rounded),
        label: const Text('New Sale', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      bottomNavigationBar: NavigationBarTheme(
        data: NavigationBarThemeData(
          indicatorColor: AppColors.primary.withOpacity(0.12),
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
              label: 'Home',
            ),
            NavigationDestination(
              icon: _navIcon(Icons.receipt_long_outlined, Icons.receipt_long_rounded, 1),
              label: 'Sales',
            ),
            NavigationDestination(
              icon: _navIcon(Icons.inventory_2_outlined, Icons.inventory_2_rounded, 2),
              label: 'Stock',
            ),
            NavigationDestination(
              icon: _navIcon(Icons.people_outline_rounded, Icons.people_rounded, 3),
              label: 'Khata',
            ),
            NavigationDestination(
              icon: _navIcon(Icons.grid_view_outlined, Icons.grid_view_rounded, 4),
              label: 'More',
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
