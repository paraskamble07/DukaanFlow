import 'dart:async';

import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' as p;

/// Local-first SQLite store for ShopZen — the ONLY source of truth.
/// Everything (products, stock, customers, khata, sales, purchases,
/// suppliers, expenses, payments, IMEI devices, stock movements) lives on
/// the user's Android device. No server required, ever.
class AppLocalDb {
  static Database? _db;
  static const int version = 1;

  static Future<Database> get db async {
    if (_db != null) return _db!;
    final dir = await getDatabasesPath();
    _db = await openDatabase(
      p.join(dir, 'shopzen.db'),
      version: version,
      onConfigure: (d) async {
        await d.execute('PRAGMA foreign_keys = ON');
      },
      onCreate: _createAll,
      onUpgrade: (d, oldV, newV) async {
        // Future schema changes go here; version 1 is the initial schema.
      },
    );
    return _db!;
  }

  static Future<void> _createAll(Database d, int version) async {
    await d.execute('''
      CREATE TABLE shop_profile (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        name TEXT NOT NULL,
        owner_name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        city TEXT DEFAULT '',
        state TEXT DEFAULT '',
        pincode TEXT DEFAULT '',
        gstin TEXT DEFAULT '',
        invoice_prefix TEXT DEFAULT 'SZ-',
        invoice_footer TEXT DEFAULT 'Thank you for your business! Visit again.',
        next_invoice_number INTEGER DEFAULT 1001,
        created_at TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        brand TEXT DEFAULT '',
        model TEXT DEFAULT '',
        category TEXT DEFAULT 'General',
        description TEXT DEFAULT '',
        purchase_price REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        stock_quantity INTEGER DEFAULT 0,
        low_stock_threshold INTEGER DEFAULT 5,
        imei_tracked INTEGER DEFAULT 0,
        barcode TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT DEFAULT '',
        address TEXT DEFAULT '',
        created_at TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        name TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        address TEXT DEFAULT '',
        created_at TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL UNIQUE,
        client_request_id TEXT,
        customer_id INTEGER NOT NULL,
        customer_name TEXT NOT NULL,
        subtotal REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        due_amount REAL DEFAULT 0,
        payment_status TEXT DEFAULT 'PAID',
        payment_method TEXT DEFAULT 'CASH',
        notes TEXT DEFAULT '',
        sale_date TEXT NOT NULL,
        items_json TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        customer_id INTEGER,
        customer_name TEXT DEFAULT '',
        supplier_id INTEGER,
        supplier_name TEXT DEFAULT '',
        sale_invoice TEXT DEFAULT '',
        amount REAL NOT NULL,
        method TEXT DEFAULT 'CASH',
        note TEXT DEFAULT '',
        paid_at TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier_id INTEGER NOT NULL,
        supplier_name TEXT NOT NULL,
        invoice_note TEXT DEFAULT '',
        total_amount REAL DEFAULT 0,
        items_json TEXT NOT NULL,
        purchase_date TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        description TEXT DEFAULT '',
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        imei_1 TEXT DEFAULT '',
        imei_2 TEXT DEFAULT '',
        serial_number TEXT DEFAULT '',
        status TEXT DEFAULT 'IN_STOCK',
        purchase_date TEXT,
        sale_invoice TEXT,
        warranty_expiry TEXT,
        created_at TEXT NOT NULL
      )
    ''');
    await d.execute('''
      CREATE TABLE stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        movement_type TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        previous_stock INTEGER NOT NULL,
        new_stock INTEGER NOT NULL,
        notes TEXT DEFAULT '',
        reference_id TEXT DEFAULT '',
        moved_at TEXT NOT NULL
      )
    ''');
  }

  // ---------- helpers ----------
  static String nowIso() => DateTime.now().toIso8601String();

  static Map<String, dynamic> rowToMap(Map<String, Object?> r) =>
      r.cast<String, dynamic>();

  static Future<List<Map<String, dynamic>>> q(
      String sql, [List<Object?>? args]) async {
    final d = await db;
    final rows = await d.rawQuery(sql, args);
    return rows.map(rowToMap).toList();
  }

  static Future<Map<String, dynamic>?> q1(
      String sql, [List<Object?>? args]) async {
    final list = await q(sql, args);
    return list.isEmpty ? null : list.first;
  }

  static Future<int> insert(String table, Map<String, Object?> values) async {
    final d = await db;
    return d.insert(table, values);
  }

  static Future<int> update(
      String table, Map<String, Object?> values, String where,
      [List<Object?>? args]) async {
    final d = await db;
    return d.update(table, values, where: where, whereArgs: args);
  }

  static Future<int> delete(String table, String where,
      [List<Object?>? args]) async {
    final d = await db;
    return d.delete(table, where: where, whereArgs: args);
  }

  static Future<T> txn<T>(Future<T> Function(Transaction) body) async {
    final d = await db;
    return d.transaction(body);
  }

  static Future<void> resetAll() async {
    final d = await db;
    await d.transaction((t) async {
      for (final t2 in [
        'stock_movements', 'devices', 'expenses', 'purchases',
        'payments', 'sales', 'suppliers', 'customers', 'products',
        'shop_profile',
      ]) {
        await t.delete(t2);
      }
    });
  }

  /// Full backup as a portable JSON document.
  static Future<Map<String, dynamic>> exportAll() async {
    final tables = [
      'shop_profile', 'products', 'customers', 'suppliers', 'sales',
      'payments', 'purchases', 'expenses', 'devices', 'stock_movements',
    ];
    final out = <String, dynamic>{
      'app': 'ShopZen',
      'schema_version': version,
      'exported_at': nowIso(),
    };
    for (final t in tables) {
      out[t] = await q('SELECT * FROM $t');
    }
    return out;
  }

  /// Restore from a backup document. Wipes current data first — this is a
  /// full restore, pointed at the file the user picked.
  static Future<void> importAll(Map<String, dynamic> backup) async {
    if (backup['app'] != 'ShopZen') {
      throw const FormatException('Not a ShopZen backup file.');
    }
    await resetAll();
    final d = await db;
    await d.transaction((t) async {
      Future<void> loadTable(String name, List<dynamic>? rows) async {
        if (rows == null) return;
        for (final r in rows) {
          final m = (r as Map).cast<String, Object?>();
          // Insert preserving original ids so invoice/IMEI references stay
          // consistent; AUTOINCREMENT continues past the restored maximum.
          m.remove('is_active_extra');
          await t.insert(name, m,
              conflictAlgorithm: ConflictAlgorithm.replace);
        }
      }

      await loadTable('shop_profile', backup['shop_profile']);
      await loadTable('products', backup['products']);
      await loadTable('customers', backup['customers']);
      await loadTable('suppliers', backup['suppliers']);
      await loadTable('sales', backup['sales']);
      await loadTable('payments', backup['payments']);
      await loadTable('purchases', backup['purchases']);
      await loadTable('expenses', backup['expenses']);
      await loadTable('devices', backup['devices']);
      await loadTable('stock_movements', backup['stock_movements']);
    });
  }
}
