import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LocalStorageService {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'auth_token';
  static const _refreshKey = 'refresh_token';
  static const _userKey = 'user_data';
  static const _businessKey = 'business_data';
  static const _offlinePosQueueKey = 'offline_pos_queue';

  static Future<void> saveTokens(String access, String refresh) async {
    await _storage.write(key: _tokenKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  static Future<String?> getAccessToken() async {
    return await _storage.read(key: _tokenKey);
  }

  static Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshKey);
  }

  static Future<void> clearAuth() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _refreshKey);
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userKey);
    await prefs.remove(_businessKey);
  }

  static Future<void> saveUser(Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userKey, jsonEncode(user));
  }

  static Future<Map<String, dynamic>?> getUser() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_userKey);
    return data != null ? jsonDecode(data) : null;
  }

  static Future<void> saveBusiness(Map<String, dynamic> business) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_businessKey, jsonEncode(business));
  }

  static Future<Map<String, dynamic>?> getBusiness() async {
    final prefs = await SharedPreferences.getInstance();
    final data = prefs.getString(_businessKey);
    return data != null ? jsonDecode(data) : null;
  }

  // Offline POS Sync Queue
  static Future<void> queueOfflineSale(Map<String, dynamic> salePayload) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_offlinePosQueueKey) ?? [];
    list.add(jsonEncode(salePayload));
    await prefs.setStringList(_offlinePosQueueKey, list);
  }

  static Future<List<Map<String, dynamic>>> getOfflineSalesQueue() async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_offlinePosQueueKey) ?? [];
    return list.map((item) => jsonDecode(item) as Map<String, dynamic>).toList();
  }

  static Future<void> clearOfflineSalesQueue() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_offlinePosQueueKey);
  }
}
