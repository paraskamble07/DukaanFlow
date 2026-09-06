import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsState {
  final ThemeMode themeMode;
  final Locale locale;

  SettingsState({
    this.themeMode = ThemeMode.system,
    this.locale = const Locale('en'),
  });

  SettingsState copyWith({ThemeMode? themeMode, Locale? locale}) {
    return SettingsState(
      themeMode: themeMode ?? this.themeMode,
      locale: locale ?? this.locale,
    );
  }
}

class SettingsNotifier extends StateNotifier<SettingsState> {
  SettingsNotifier() : super(SettingsState()) {
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final theme = prefs.getString('pref_theme') ?? 'system';
    final lang = prefs.getString('pref_lang') ?? 'en';

    ThemeMode mode = ThemeMode.system;
    if (theme == 'light') mode = ThemeMode.light;
    if (theme == 'dark') mode = ThemeMode.dark;

    state = SettingsState(themeMode: mode, locale: Locale(lang));
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    state = state.copyWith(themeMode: mode);
    final prefs = await SharedPreferences.getInstance();
    String val = 'system';
    if (mode == ThemeMode.light) val = 'light';
    if (mode == ThemeMode.dark) val = 'dark';
    await prefs.setString('pref_theme', val);
  }

  Future<void> setLocale(String langCode) async {
    state = state.copyWith(locale: Locale(langCode));
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('pref_lang', langCode);
  }
}

final settingsProvider = StateNotifierProvider<SettingsNotifier, SettingsState>((ref) {
  return SettingsNotifier();
});
