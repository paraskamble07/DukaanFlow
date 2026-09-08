import 'dart:async';
import 'dart:convert';

import '../storage/app_local_db.dart';

/// Local-first API adapter.
///
/// ShopZen v2 stores EVERYTHING in the on-device SQLite database. To keep
/// the existing screens and providers untouched, this class mimics the tiny
/// slice of the Dio interface the app used (`get`/`post`/`put`/`delete`) and
/// routes each URL to a local database handler that returns EXACTLY the
/// same response shape the server used to. No network. No server. Offline
/// forever. A future cloud-sync layer can be added beside this adapter
/// without touching any screen.
class LocalDio {
  Future<LocalResponse> get(String path,
      {Map<String, dynamic>? queryParameters}) async {
    final data = await _route('GET', path, queryParameters ?? {}, null);
    return LocalResponse(200, data);
  }

  Future<LocalResponse> post(String path,
      {Object? data, Map<String, dynamic>? queryParameters}) async {
    final res = await _route('POST', path, queryParameters ?? {}, data);
    return LocalResponse(res.isEmpty ? 400 : 201, res);
  }

  Future<LocalResponse> put(String path, {Object? data}) async {
    await _route('PUT', path, {}, data);
    return LocalResponse(200, {});
  }

  Future<LocalResponse> delete(String path) async {
    await _route('DELETE', path, {}, null);
    return LocalResponse(204, {});
  }

  Future<Map<String, dynamic>> _route(String method, String path,
      Map<String, dynamic> query, Object? body) async {
    final p = path.startsWith('/') ? path : '/$path';
    final bodyMap = body is Map<String, dynamic> ? body : <String, dynamic>{};
    final q = query.map((k, v) => MapEntry(k, v.toString()));

    // ---------- Products ----------
    if (p == '/api/products/' && method == 'GET') {
      return _productList(q);
    }
    if (p == '/api/products/' && method == 'POST') return _productCreate(bodyMap);
    final prodId = _idFrom(p, '/api/products/');
    if (prodId != null) {
      if (method == 'PUT') return _productUpdate(prodId, bodyMap);
      if (method == 'DELETE') return _productDelete(prodId);
    }

    // ---------- Categories ----------
    if (p == '/api/categories/' && method == 'GET') return _categoryList();
    if (p == '/api/categories/' && method == 'POST') return _categoryCreate(bodyMap);

    // ---------- Stock ----------
    if (p == '/api/inventory/movements/' && method == 'GET') return _movementList(q);
    if (p.startsWith('/api/inventory/adjust/') && method == 'POST') {
      return _stockAdjust(_idFrom(p, '/api/inventory/adjust/')!, bodyMap);
    }

    // ---------- IMEI ----------
    if (p == '/api/inventory/imei/' && method == 'GET') return _deviceList(q);
    if (p == '/api/inventory/imei/' && method == 'POST') return _deviceCreate(bodyMap);
    if (p == '/api/inventory/imei/lookup/' && method == 'GET') {
      return _deviceLookup(q['imei'] ?? '');
    }

    // ---------- Customers ----------
    if (p == '/api/customers/' && method == 'GET') return _customerList(q);
    if (p == '/api/customers/' && method == 'POST') return _customerCreate(bodyMap);
    final custId = _idFrom(p, '/api/customers/');
    if (custId != null && p.endsWith('/ledger/') && method == 'GET') {
      return _customerLedger(custId);
    }
    if (custId != null && method == 'PUT') return _customerUpdate(custId, bodyMap);
    if (custId != null && method == 'DELETE') return _customerDelete(custId);

    // ---------- Suppliers ----------
    if (p == '/api/suppliers/' && method == 'GET') return _supplierList(q);
    if (p == '/api/suppliers/' && method == 'POST') return _supplierCreate(bodyMap);
    final supId = _idFrom(p, '/api/suppliers/');
    if (supId != null && method == 'GET') return _supplierDetail(supId);
    if (supId != null && method == 'PUT') return _supplierUpdate(supId, bodyMap);
    if (supId != null && method == 'DELETE') return _supplierDelete(supId);

    // ---------- Purchases ----------
    if (p == '/api/purchases/' && method == 'GET') return _purchaseList(q);
    if (p == '/api/purchases/' && method == 'POST') return _purchaseCreate(bodyMap);

    // ---------- Expenses ----------
    if (p == '/api/expenses/' && method == 'GET') return _expenseList(q);
    if (p == '/api/expenses/' && method == 'POST') return _expenseCreate(bodyMap);
    if (p == '/api/expenses/categories/' && method == 'GET') {
      return _expenseCategoryList();
    }
    final expId = _idFrom(p, '/api/expenses/');
    if (expId != null && method == 'DELETE') return _expenseDelete(expId);

    // ---------- Payments ----------
    if (p == '/api/payments/' && method == 'GET') return _paymentList(q);
    if (p == '/api/payments/customer/' && method == 'POST') {
      return _customerPaymentCreate(bodyMap);
    }
    if (p == '/api/payments/supplier/' && method == 'POST') {
      return _supplierPaymentCreate(bodyMap);
    }

    // ---------- POS + Sales ----------
    if (p == '/api/pos/checkout/' && method == 'POST') return _checkout(bodyMap);
    if (p == '/api/sales/' && method == 'GET') return _saleList(q);
    final saleId = _idFrom(p, '/api/sales/');
    if (saleId != null && method == 'GET') return _saleDetail(saleId);

    // ---------- Dashboard & reports ----------
    if (p == '/api/dashboard/' && method == 'GET') return _dashboard();
    if (p == '/api/reports/profit-loss/' && method == 'GET') return _profitLoss(q);
    if (p == '/api/reports/sales/' && method == 'GET') return _salesReport(q);
    if (p == '/api/reports/stock/' && method == 'GET') return _stockReport();
    if (p == '/api/reports/khata/' && method == 'GET') return _khataReport();
    if (p == '/api/reports/expenses/' && method == 'GET') return _expenseReport(q);
    if (p == '/api/reports/gst/' && method == 'GET') return _gstReport(q);
    if (p == '/api/reports/top-products/' && method == 'GET') return _topProducts(q);
    if (p == '/api/reports/top-customers/' && method == 'GET') return _topCustomers(q);

    // ---------- Subscription: lifetime local license — no server, no expiry ----------
    if (p == '/api/subscription/status/') return _subscriptionStatus();
    if (p == '/api/subscription/payment-config/') return _subscriptionStatus();

    // ---------- Auth/profile (local-only) ----------
    if (p == '/api/auth/profile/' && method == 'GET') return _profile();
    if (p == '/api/auth/register/' && method == 'POST') return _register(bodyMap);

    if (p == '/api/business/settings/' && method == 'GET') return _businessGet();
    if (p == '/api/business/settings/' && method == 'PUT') return _businessPut(bodyMap);
    if (p == '/api/business/plans/' && method == 'GET') return {'plans': []};

    throw UnsupportedError('Local mode has no handler for $method $p');
  }

  static int? _idFrom(String p, String base) {
    final rest = p.substring(base.length);
    if (rest.isEmpty || rest.contains('/ledger')) {
      if (rest.contains('/ledger')) {
        return int.tryParse(p.substring(base.length).split('/').first);
      }
      return null;
    }
    return int.tryParse(rest.split('/').first);
  }

  static double _d(dynamic v) => double.tryParse(v?.toString() ?? '0') ?? 0.0;

  // ================= SHOP PROFILE =================
  static Future<Map<String, dynamic>> _profileRow() async {
    return await AppLocalDb.q1('SELECT * FROM shop_profile WHERE id = 1') ??
        {};
  }

  Future<Map<String, dynamic>> _profile() async {
    final s = await _profileRow();
    if (s.isEmpty) return {'user': null, 'business': null};
    return {
      'user': {
        'id': 1,
        'username': s['owner_name'],
        'email': s['email'] ?? '',
        'first_name': s['owner_name'],
        'last_name': '',
        'profile': {'phone': s['phone'] ?? '', 'role': 'OWNER', 'created_at': s['created_at']},
        'is_shopzen_admin': false,
      },
      'business': _businessMap(s),
    };
  }

  Map<String, dynamic> _businessMap(Map<String, dynamic> s) => {
        'id': 1,
        'name': s['name'],
        'owner_name': s['owner_name'],
        'phone': s['phone'] ?? '',
        'email': s['email'] ?? '',
        'address': s['address'] ?? '',
        'city': s['city'] ?? '',
        'state': s['state'] ?? '',
        'pincode': s['pincode'] ?? '',
        'gstin': s['gstin'] ?? '',
        'logo': null,
        'logo_url': null,
        'invoice_prefix': s['invoice_prefix'] ?? 'SZ-',
        'invoice_footer': s['invoice_footer'] ?? '',
        'plan_tier': 'LOCAL',
        'plan_info': {'name': 'ShopZen Local', 'price': 0},
        'created_at': s['created_at'],
        'updated_at': s['created_at'],
      };

  Future<Map<String, dynamic>> _register(Map<String, dynamic> b) async {
    await AppLocalDb.insert('shop_profile', {
      'id': 1,
      'name': (b['shop_name'] ?? 'My Shop').toString(),
      'owner_name': (b['full_name'] ?? 'Owner').toString(),
      'phone': (b['phone'] ?? '').toString(),
      'email': (b['email'] ?? '').toString(),
      'created_at': AppLocalDb.nowIso(),
    });
    final prof = await _profile();
    return {'user': prof['user'], 'business': prof['business']};
  }

  Future<Map<String, dynamic>> _businessGet() async {
    final s = await _profileRow();
    return _businessMap(s);
  }

  Future<Map<String, dynamic>> _businessPut(Map<String, dynamic> b) async {
    final s = await _profileRow();
    if (s.isEmpty) return {};
    final map = {
      if (b['name'] != null) 'name': b['name'],
      if (b['owner_name'] != null) 'owner_name': b['owner_name'],
      if (b['phone'] != null) 'phone': b['phone'],
      if (b['email'] != null) 'email': b['email'],
      if (b['address'] != null) 'address': b['address'],
      if (b['city'] != null) 'city': b['city'],
      if (b['state'] != null) 'state': b['state'],
      if (b['pincode'] != null) 'pincode': b['pincode'],
      if (b['gstin'] != null) 'gstin': b['gstin'],
      if (b['invoice_prefix'] != null) 'invoice_prefix': b['invoice_prefix'],
      if (b['invoice_footer'] != null) 'invoice_footer': b['invoice_footer'],
    };
    await AppLocalDb.update('shop_profile', map, 'id = 1');
    return _businessGet();
  }

  // ================= PRODUCTS =================
  Map<String, dynamic> _productJson(Map<String, dynamic> r) {
    final stock = (r['stock_quantity'] ?? 0) as int;
    final minS = (r['low_stock_threshold'] ?? 5) as int;
    final sell = _d(r['selling_price']);
    final cost = _d(r['purchase_price']);
    final margin = sell > 0 ? ((sell - cost) / sell) * 100 : 0.0;
    return {
      'id': r['id'],
      'name': r['name'],
      'brand': r['brand'],
      'category': r['category_id'],
      'category_name': r['category'],
      'sku': r['sku'] ?? '',
      'barcode': r['barcode'] ?? '',
      'purchase_price': cost,
      'selling_price': sell,
      'stock_quantity': stock,
      'min_stock': minS,
      'warranty_months': (r['warranty_months'] ?? 0) as int,
      'is_imei_tracked': (r['imei_tracked'] ?? 0) == 1,
      'supplier': r['supplier_id'],
      'supplier_name': r['supplier_name'] ?? '',
      'image': null,
      'image_url': null,
      'description': r['description'] ?? '',
      'is_low_stock': stock > 0 && stock <= minS,
      'is_out_of_stock': stock <= 0,
      'profit_margin': margin.roundToDouble() * 10 / 10,
      'created_at': r['created_at'],
      'updated_at': r['created_at'],
    };
  }

  static const _defaultCat = 'General';

  Future<Map<String, dynamic>> _productList(Map<String, dynamic> q) async {
    final search = (q['search'] ?? '').toString().trim();
    final cat = (q['category'] ?? '').toString();
    var sql = 'SELECT * FROM products WHERE is_active = 1';
    final args = <Object?>[];
    if (search.isNotEmpty) {
      sql += ' AND (name LIKE ? OR brand LIKE ? OR barcode LIKE ?)';
      args.add('%$search%');
      args.add('%$search%');
      args.add('%$search%');
    }
    if (cat.isNotEmpty && cat != '0') {
      sql += ' AND category = ?';
      args.add(cat);
    }
    sql += ' ORDER BY id DESC';
    final rows = await AppLocalDb.q(sql, args);
    return {'results': rows.map(_productJson).toList()};
  }

  Future<Map<String, dynamic>> _productCreate(Map<String, dynamic> b) async {
    final id = await AppLocalDb.insert('products', {
      'name': (b['name'] ?? '').toString(),
      'brand': (b['brand'] ?? '').toString(),
      'model': (b['model'] ?? '').toString(),
      'category': (b['category_name'] ?? b['category'] ?? _defaultCat).toString(),
      'description': (b['description'] ?? '').toString(),
      'purchase_price': _d(b['purchase_price']),
      'selling_price': _d(b['selling_price']),
      'stock_quantity': (b['stock_quantity'] is int)
          ? b['stock_quantity']
          : int.tryParse(b['stock_quantity']?.toString() ?? '0') ?? 0,
      'low_stock_threshold': int.tryParse(b['min_stock']?.toString() ?? '5') ?? 5,
      'imei_tracked': (b['is_imei_tracked'] == true || b['is_imei_tracked'] == 1) ? 1 : 0,
      'barcode': (b['barcode'] ?? '').toString(),
      'created_at': AppLocalDb.nowIso(),
    });
    final row = await AppLocalDb.q1('SELECT * FROM products WHERE id = ?', [id]);
    return _productJson(row!);
  }

  Future<Map<String, dynamic>> _productUpdate(int id, Map<String, dynamic> b) async {
    final existing = await AppLocalDb.q1('SELECT * FROM products WHERE id = ?', [id]);
    if (existing == null) return {};
    await AppLocalDb.update(
        'products',
        {
          'name': (b['name'] ?? existing['name']).toString(),
          'brand': (b['brand'] ?? existing['brand'] ?? '').toString(),
          'category': (b['category_name'] ?? existing['category']).toString(),
          'description': (b['description'] ?? existing['description'] ?? '').toString(),
          'purchase_price': b['purchase_price'] != null ? _d(b['purchase_price']) : existing['purchase_price'],
          'selling_price': b['selling_price'] != null ? _d(b['selling_price']) : existing['selling_price'],
          'low_stock_threshold': b['min_stock'] != null
              ? int.tryParse(b['min_stock'].toString()) ?? existing['low_stock_threshold']
              : existing['low_stock_threshold'],
          'barcode': (b['barcode'] ?? existing['barcode'] ?? '').toString(),
        },
        'id = ?',
        [id]);
    final row = await AppLocalDb.q1('SELECT * FROM products WHERE id = ?', [id]);
    return _productJson(row!);
  }

  Future<Map<String, dynamic>> _productDelete(int id) async {
    await AppLocalDb.delete('products', 'id = ?', [id]);
    return {};
  }

  Future<Map<String, dynamic>> _stockAdjust(int productId, Map<String, dynamic> b) async {
    final delta = int.tryParse(b['quantity']?.toString() ?? '0') ?? 0;
    final reason = (b['reason'] ?? 'Manual adjustment').toString();
    final res = await _adjustStock(productId, delta, reason, 'ADJUSTMENT');
    return res;
  }

  Future<Map<String, dynamic>> _adjustStock(
      int productId, int delta, String reason, String type) async {
    final prod = await AppLocalDb.q1('SELECT * FROM products WHERE id = ?', [productId]);
    if (prod == null) return {};
    final old = (prod['stock_quantity'] ?? 0) as int;
    final newStock = old + delta;
    if (newStock < 0) {
      throw LocalApiError(400, 'Insufficient stock available.');
    }
    await AppLocalDb.update(
        'products', {'stock_quantity': newStock}, 'id = ?', [productId]);
    await AppLocalDb.insert('stock_movements', {
      'product_id': productId,
      'product_name': prod['name'],
      'movement_type': type,
      'quantity': delta.abs(),
      'previous_stock': old,
      'new_stock': newStock,
      'notes': reason,
      'reference_id': '',
      'moved_at': AppLocalDb.nowIso(),
    });
    return {'new_stock': newStock, 'product_name': prod['name']};
  }

  Future<Map<String, dynamic>> _movementList(Map<String, dynamic> q) async {
    final pid = int.tryParse(q['product'] ?? '');
    var sql = 'SELECT * FROM stock_movements';
    final args = <Object?>[];
    if (pid != null) {
      sql += ' WHERE product_id = ?';
      args.add(pid);
    }
    sql += ' ORDER BY id DESC LIMIT 100';
    final rows = await AppLocalDb.q(sql, args);
    return {
      'results': rows.map((r) => {
            'id': r['id'],
            'product': r['product_id'],
            'product_name': r['product_name'],
            'movement_type': r['movement_type'],
            'quantity': r['quantity'],
            'previous_stock': r['previous_stock'],
            'new_stock': r['new_stock'],
            'notes': r['notes'],
            'moved_at': r['moved_at'],
          }).toList()
    };
  }

  // ================= CATEGORIES =================
  Future<Map<String, dynamic>> _categoryList() async {
    final rows = await AppLocalDb.q(
        'SELECT category AS name, COUNT(*) AS product_count FROM products GROUP BY category ORDER BY category');
    return {
      'results': rows
          .map((r) => {
                'id': r['name'],
                'name': r['name'],
                'description': '',
                'product_count': r['product_count'],
              })
          .toList()
    };
  }

  Future<Map<String, dynamic>> _categoryCreate(Map<String, dynamic> b) async {
    // Categories are a label on products; nothing to create standalone.
    return {'id': b['name'], 'name': b['name'], 'description': '', 'product_count': 0};
  }

  // ================= IMEI DEVICES =================
  Future<Map<String, dynamic>> _deviceList(Map<String, dynamic> q) async {
    final search = (q['search'] ?? '').toString().trim();
    var sql = 'SELECT * FROM devices';
    final args = <Object?>[];
    if (search.isNotEmpty) {
      sql += ' WHERE imei_1 LIKE ? OR imei_2 LIKE ? OR serial_number LIKE ?';
      args.add('%$search%');
      args.add('%$search%');
      args.add('%$search%');
    }
    sql += ' ORDER BY id DESC LIMIT 100';
    final rows = await AppLocalDb.q(sql, args);
    return {'results': rows.map(_deviceJson).toList()};
  }

  Map<String, dynamic> _deviceJson(Map<String, dynamic> r) => {
        'id': r['id'],
        'product': r['product_id'],
        'product_name': r['product_name'] ?? '',
        'imei_1': r['imei_1'],
        'imei_2': r['imei_2'],
        'serial_number': r['serial_number'],
        'status': r['status'],
        'status_display': r['status'],
        'invoice_number': r['sale_invoice'],
        'purchase_date': r['purchase_date'],
        'warranty_expiry_date': r['warranty_expiry'],
        'created_at': r['created_at'],
      };

  Future<Map<String, dynamic>> _deviceCreate(Map<String, dynamic> b) async {
    final imei1 = (b['imei_1'] ?? '').toString();
    final dupe = await AppLocalDb.q1(
        'SELECT id FROM devices WHERE imei_1 = ? OR (imei_2 != \'\' AND imei_2 = ?)',
        [imei1, imei1]);
    if (dupe != null) {
      throw LocalApiError(400, 'This IMEI is already registered in your inventory.');
    }
    final id = await AppLocalDb.insert('devices', {
      'product_id': int.tryParse(b['product']?.toString() ?? '0') ?? 0,
      'imei_1': imei1,
      'imei_2': (b['imei_2'] ?? '').toString(),
      'serial_number': (b['serial_number'] ?? '').toString(),
      'status': 'IN_STOCK',
      'purchase_date': AppLocalDb.nowIso(),
      'created_at': AppLocalDb.nowIso(),
    });
    final row = await AppLocalDb.q1('SELECT * FROM devices WHERE id = ?', [id]);
    return _deviceJson(row!);
  }

  Future<Map<String, dynamic>> _deviceLookup(String imei) async {
    final rows = await AppLocalDb.q(
        'SELECT * FROM devices WHERE imei_1 = ? OR imei_2 = ? LIMIT 1', [imei, imei]);
    if (rows.isEmpty) {
      throw LocalApiError(404, 'No device found with this IMEI in your records.');
    }
    return _deviceJson(rows.first);
  }

  // ================= CUSTOMERS =================
  Map<String, dynamic> _customerJson(
      Map<String, dynamic> r, Map<String, dynamic> agg) {
    return {
      'id': r['id'],
      'name': r['name'],
      'phone': r['phone'],
      'email': '',
      'address': r['address'] ?? '',
      'notes': '',
      'credit_limit': 0,
      'total_sales': _d(agg['total_sales']),
      'total_paid': _d(agg['total_paid']),
      'outstanding_due': _d(agg['due']),
      'whatsapp_reminder_url':
          'https://wa.me/${(r['phone'] ?? '').toString().replaceAll(RegExp(r'[^0-9]'), '')}',
      'created_at': r['created_at'],
      'updated_at': r['created_at'],
    };
  }

  static Future<Map<String, dynamic>> _customerAgg(int customerId) async {
    final sales = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(total_amount),0) AS t, COALESCE(SUM(paid_amount),0) AS p '
        'FROM sales WHERE customer_id = ?', [customerId]);
    return {'total_sales': sales?['t'] ?? 0, 'total_paid': sales?['p'] ?? 0};
  }

  Future<Map<String, dynamic>> _customerList(Map<String, dynamic> q) async {
    final search = (q['search'] ?? '').toString().trim();
    var sql = 'SELECT * FROM customers';
    final args = <Object?>[];
    if (search.isNotEmpty) {
      sql += ' WHERE name LIKE ? OR phone LIKE ?';
      args.add('%$search%');
      args.add('%$search%');
    }
    sql += ' ORDER BY id DESC';
    final rows = await AppLocalDb.q(sql, args);
    final out = <Map<String, dynamic>>[];
    for (final r in rows) {
      final agg = await _customerAgg(r['id'] as int);
      final due = _d(agg['total_sales']) - _d(agg['total_paid']);
      agg['due'] = due;
      out.add(_customerJson(r, agg));
    }
    return {'results': out};
  }

  Future<Map<String, dynamic>> _customerCreate(Map<String, dynamic> b) async {
    final id = await AppLocalDb.insert('customers', {
      'name': (b['name'] ?? '').toString(),
      'phone': (b['phone'] ?? '').toString(),
      'address': (b['address'] ?? '').toString(),
      'created_at': AppLocalDb.nowIso(),
    });
    final row = await AppLocalDb.q1('SELECT * FROM customers WHERE id = ?', [id]);
    return _customerJson(row!, {'total_sales': 0, 'total_paid': 0, 'due': 0});
  }

  Future<Map<String, dynamic>> _customerUpdate(int id, Map<String, dynamic> b) async {
    await AppLocalDb.update(
        'customers',
        {
          'name': (b['name'] ?? '').toString(),
          'phone': (b['phone'] ?? '').toString(),
          'address': (b['address'] ?? '').toString(),
        },
        'id = ?',
        [id]);
    return {};
  }

  Future<Map<String, dynamic>> _customerDelete(int id) async {
    await AppLocalDb.delete('customers', 'id = ?', [id]);
    return {};
  }

  Future<Map<String, dynamic>> _customerLedger(int customerId) async {
    final cust = await AppLocalDb.q1('SELECT * FROM customers WHERE id = ?', [customerId]);
    if (cust == null) {
      throw LocalApiError(404, 'Customer not found.');
    }
    final sales = await AppLocalDb.q(
        'SELECT * FROM sales WHERE customer_id = ? ORDER BY id DESC LIMIT 50', [customerId]);
    final pays = await AppLocalDb.q(
        'SELECT * FROM payments WHERE customer_id = ? ORDER BY id DESC LIMIT 50', [customerId]);
    final agg = await _customerAgg(customerId);
    final saleTotal = _d(agg['total_sales']);
    final paidRows = await AppLocalDb.q(
        'SELECT COALESCE(SUM(amount),0) AS s FROM payments WHERE customer_id = ?',
        [customerId]);
    final paidTotal = _d(paidRows.first?['s']);
    final due = saleTotal - paidTotal;
    return {
      'summary': {
        'total_sales': saleTotal,
        'total_paid': paidTotal,
        'outstanding_due': due,
        'whatsapp_reminder_url':
            'https://wa.me/${(cust['phone'] ?? '').toString().replaceAll(RegExp(r'[^0-9]'), '')}',
      },
      'sales': sales.map(_saleJson).toList(),
      'payments': pays
          .map((p) => {
                'id': p['id'],
                'amount': _d(p['amount']),
                'payment_method': p['method'],
                'paid_at': p['paid_at'],
                'note': p['note'],
              })
          .toList(),
    };
  }

  // ================= SUPPLIERS =================
  Map<String, dynamic> _supplierJson(
      Map<String, dynamic> r, double purchased, double paid) => {
        'id': r['id'],
        'company_name': r['company_name'],
        'name': r['name'],
        'phone': r['phone'],
        'email': r['email'] ?? '',
        'address': r['address'] ?? '',
        'total_purchases': purchased,
        'total_paid': paid,
        'outstanding_due': purchased - paid,
        'created_at': r['created_at'],
      };

  Future<Map<String, dynamic>> _supplierList(Map<String, dynamic> q) async {
    final search = (q['search'] ?? '').toString().trim();
    var sql = 'SELECT * FROM suppliers';
    final args = <Object?>[];
    if (search.isNotEmpty) {
      sql += ' WHERE company_name LIKE ? OR name LIKE ? OR phone LIKE ?';
      args.add('%$search%');
      args.add('%$search%');
      args.add('%$search%');
    }
    sql += ' ORDER BY id DESC';
    final rows = await AppLocalDb.q(sql, args);
    final out = <Map<String, dynamic>>[];
    for (final r in rows) {
      final id = r['id'] as int;
      final pur = await AppLocalDb.q1(
          'SELECT COALESCE(SUM(total_amount),0) AS t FROM purchases WHERE supplier_id = ?',
          [id]);
      final pay = await AppLocalDb.q1(
          'SELECT COALESCE(SUM(amount),0) AS s FROM payments WHERE supplier_id = ?',
          [id]);
      out.add(_supplierJson(r, _d(pur?['t']), _d(pay?['s'])));
    }
    return {'results': out};
  }

  Future<Map<String, dynamic>> _supplierCreate(Map<String, dynamic> b) async {
    final id = await AppLocalDb.insert('suppliers', {
      'company_name': (b['company_name'] ?? '').toString(),
      'name': (b['name'] ?? '').toString(),
      'phone': (b['phone'] ?? '').toString(),
      'email': (b['email'] ?? '').toString(),
      'address': (b['address'] ?? '').toString(),
      'created_at': AppLocalDb.nowIso(),
    });
    final row = await AppLocalDb.q1('SELECT * FROM suppliers WHERE id = ?', [id]);
    return _supplierJson(row!, 0, 0);
  }

  Future<Map<String, dynamic>> _supplierUpdate(int id, Map<String, dynamic> b) async {
    await AppLocalDb.update(
        'suppliers',
        {
          'company_name': (b['company_name'] ?? '').toString(),
          'name': (b['name'] ?? '').toString(),
          'phone': (b['phone'] ?? '').toString(),
          'email': (b['email'] ?? '').toString(),
          'address': (b['address'] ?? '').toString(),
        },
        'id = ?',
        [id]);
    return {};
  }

  Future<Map<String, dynamic>> _supplierDelete(int id) async {
    await AppLocalDb.delete('suppliers', 'id = ?', [id]);
    return {};
  }

  Future<Map<String, dynamic>> _supplierDetail(int id) async {
    final rows = await AppLocalDb.q1('SELECT * FROM suppliers WHERE id = ?', [id]);
    if (rows == null) throw LocalApiError(404, 'Supplier not found.');
    final pur = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(total_amount),0) AS t FROM purchases WHERE supplier_id = ?',
        [id]);
    final pay = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(amount),0) AS s FROM payments WHERE supplier_id = ?',
        [id]);
    return _supplierJson(rows, _d(pur?['t']), _d(pay?['s']));
  }

  // ================= PURCHASES =================
  Future<Map<String, dynamic>> _purchaseList(Map<String, dynamic> q) async {
    final rows = await AppLocalDb.q('SELECT * FROM purchases ORDER BY id DESC LIMIT 100');
    return {
      'results': rows.map((r) {
        final items = jsonDecode(r['items_json'] as String) as List<dynamic>;
        return {
          'id': r['id'],
          'supplier': r['supplier_id'],
          'supplier_name': r['supplier_name'],
          'invoice_number': r['invoice_note'],
          'total_amount': _d(r['total_amount']),
          'items_count': items.length,
          'purchase_date': r['purchase_date'],
        };
      }).toList()
    };
  }

  Future<Map<String, dynamic>> _purchaseCreate(Map<String, dynamic> b) async {
    final supplierId = int.tryParse(b['supplier_id']?.toString() ?? '0') ?? 0;
    final sup = await AppLocalDb.q1('SELECT * FROM suppliers WHERE id = ?', [supplierId]);
    if (sup == null) throw LocalApiError(400, 'Please select a supplier first.');
    final items = (b['items'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    double total = 0;
    for (final it in items) {
      total += _d(it['unit_price']) * (_d(it['quantity']));
    }
    // Stock increases happen inside one transaction with the record itself.
    final id = await AppLocalDb.txn((t) async {
      final pid = await t.insert('purchases', {
        'supplier_id': supplierId,
        'supplier_name': sup['company_name'],
        'invoice_note': (b['invoice_note'] ?? '').toString(),
        'total_amount': total,
        'items_json': jsonEncode(items),
        'purchase_date': AppLocalDb.nowIso(),
      });
      for (final it in items) {
        final prodId = int.tryParse(it['product_id']?.toString() ?? '0') ?? 0;
        final qty = int.tryParse(it['quantity']?.toString() ?? '0') ?? 0;
        if (prodId <= 0 || qty <= 0) continue;
        final prod = await t.query('products', where: 'id = ?', whereArgs: [prodId]);
        if (prod.isEmpty) continue;
        final old = (prod.first['stock_quantity'] ?? 0) as int;
        await t.update('products', {'stock_quantity': old + qty}, where: 'id = ?', whereArgs: [prodId]);
        await t.insert('stock_movements', {
          'product_id': prodId,
          'product_name': prod.first['name'],
          'movement_type': 'PURCHASE',
          'quantity': qty,
          'previous_stock': old,
          'new_stock': old + qty,
          'notes': 'Purchase from ${sup['company_name']}',
          'reference_id': 'PUR-$pid',
          'moved_at': AppLocalDb.nowIso(),
        });
      }
      return pid;
    });
    return {'id': id, 'total_amount': total};
  }

  Future<Map<String, dynamic>> _supplierPaymentCreate(Map<String, dynamic> b) async {
    final supplierId = int.tryParse(b['supplier_id']?.toString() ?? '0') ?? 0;
    final sup = await AppLocalDb.q1('SELECT * FROM suppliers WHERE id = ?', [supplierId]);
    await AppLocalDb.insert('payments', {
      'type': 'SUPPLIER_PAYMENT',
      'supplier_id': supplierId,
      'supplier_name': sup?['company_name'] ?? '',
      'amount': _d(b['amount']),
      'method': (b['payment_method'] ?? 'CASH').toString(),
      'note': (b['note'] ?? '').toString(),
      'paid_at': AppLocalDb.nowIso(),
    });
    return {'message': 'Supplier payment recorded.'};
  }

  // ================= EXPENSES =================
  Future<Map<String, dynamic>> _expenseList(Map<String, dynamic> q) async {
    final rows = await AppLocalDb.q('SELECT * FROM expenses ORDER BY id DESC LIMIT 200');
    return {
      'results': rows.map((r) => {
            'id': r['id'],
            'category': r['category'],
            'description': r['description'],
            'amount': _d(r['amount']),
            'expense_date': r['expense_date'],
          }).toList()
    };
  }

  Future<Map<String, dynamic>> _expenseCreate(Map<String, dynamic> b) async {
    final id = await AppLocalDb.insert('expenses', {
      'category': (b['category'] ?? 'Other').toString(),
      'description': (b['description'] ?? '').toString(),
      'amount': _d(b['amount']),
      'expense_date': (b['expense_date'] ?? AppLocalDb.nowIso()).toString(),
    });
    return {'id': id, 'message': 'Expense recorded.'};
  }

  Future<Map<String, dynamic>> _expenseDelete(int id) async {
    await AppLocalDb.delete('expenses', 'id = ?', [id]);
    return {};
  }

  Future<Map<String, dynamic>> _expenseCategoryList() async {
    final rows = await AppLocalDb.q(
        'SELECT category, COUNT(*) AS c, COALESCE(SUM(amount),0) AS total FROM expenses GROUP BY category ORDER BY category');
    return {
      'results': rows.map((r) => {
            'id': r['category'],
            'name': r['category'],
            'usage_count': r['c'],
            'total': _d(r['total']),
          }).toList()
    };
  }

  // ================= PAYMENTS =================
  Future<Map<String, dynamic>> _paymentList(Map<String, dynamic> q) async {
    final rows = await AppLocalDb.q('SELECT * FROM payments ORDER BY id DESC LIMIT 100');
    return {
      'results': rows.map((r) => {
            'id': r['id'],
            'payment_type': r['type'],
            'amount': _d(r['amount']),
            'payment_method': r['method'],
            'note': r['note'],
            'paid_at': r['paid_at'],
          }).toList()
    };
  }

  Future<Map<String, dynamic>> _customerPaymentCreate(Map<String, dynamic> b) async {
    final customerId = int.tryParse(b['customer_id']?.toString() ?? '0') ?? 0;
    final cust = await AppLocalDb.q1('SELECT * FROM customers WHERE id = ?', [customerId]);
    await AppLocalDb.insert('payments', {
      'type': 'CUSTOMER_PAYMENT',
      'customer_id': customerId,
      'customer_name': cust?['name'] ?? '',
      'amount': _d(b['amount']),
      'method': (b['payment_method'] ?? 'CASH').toString(),
      'note': (b['note'] ?? 'Khata payment received').toString(),
      'paid_at': AppLocalDb.nowIso(),
    });
    return {'message': 'Payment recorded successfully.'};
  }

  // ================= POS CHECKOUT (atomic + idempotent) =================
  Future<Map<String, dynamic>> _checkout(Map<String, dynamic> payload) async {
    final clientRequestId =
        (payload['client_request_id'] ?? '').toString().trim();
    if (clientRequestId.isNotEmpty) {
      final existing = await AppLocalDb.q1(
          'SELECT * FROM sales WHERE client_request_id = ?', [clientRequestId]);
      if (existing != null) {
        return _checkoutResponse(existing);
      }
    }

    final items = (payload['items'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>();
    if (items.isEmpty) {
      throw LocalApiError(400, 'Cart is empty. Please add products.');
    }
    final paymentMethod = (payload['payment_method'] ?? 'CASH').toString();
    final newCustName = (payload['new_customer_name'] ?? '').toString().trim();
    final newCustPhone = (payload['new_customer_phone'] ?? '').toString().trim();
    var customerId = int.tryParse(payload['customer_id']?.toString() ?? '');
    var customerName = '';
    var customerPhone = '';

    // Resolve customer BEFORE the transaction (read-only checks).
    if (customerId != null) {
      final c = await AppLocalDb.q1('SELECT * FROM customers WHERE id = ?', [customerId]);
      if (c == null) {
        throw LocalApiError(400, 'Selected customer was not found.');
      }
      customerName = c['name'] as String;
      customerPhone = (c['phone'] ?? '') as String;
    } else if (newCustName.isNotEmpty && newCustPhone.isNotEmpty) {
      final existing = await AppLocalDb.q1(
          'SELECT * FROM customers WHERE phone = ?', [newCustPhone]);
      if (existing != null) {
        customerId = existing['id'] as int;
        customerName = existing['name'] as String;
        customerPhone = (existing['phone'] ?? '') as String;
      } else {
        customerId = await AppLocalDb.insert('customers', {
          'name': newCustName,
          'phone': newCustPhone,
          'address': '',
          'created_at': AppLocalDb.nowIso(),
        });
        customerName = newCustName;
        customerPhone = newCustPhone;
      }
    } else {
      final walkIn = await AppLocalDb.q1(
          'SELECT * FROM customers WHERE phone = ?', ['0000000000']);
      if (walkIn != null) {
        customerId = walkIn['id'] as int;
        customerName = walkIn['name'] as String;
        customerPhone = '0000000000';
      } else {
        customerId = await AppLocalDb.insert('customers', {
          'name': 'Walk-in / Cash Customer',
          'phone': '0000000000',
          'address': '',
          'created_at': AppLocalDb.nowIso(),
        });
        customerName = 'Walk-in / Cash Customer';
        customerPhone = '0000000000';
      }
    }

    // Validate stock for every line BEFORE writing anything.
    double subtotal = 0;
    final lines = <Map<String, dynamic>>[];
    for (final it in items) {
      final pid = int.tryParse(it['product_id']?.toString() ?? '0') ?? 0;
      final qty = int.tryParse(it['quantity']?.toString() ?? '0') ?? 0;
      final price = _d(it['unit_price']);
      final disc = _d(it['discount']);
      final prod = await AppLocalDb.q1('SELECT * FROM products WHERE id = ?', [pid]);
      if (prod == null) {
        throw LocalApiError(400,
            "One of the products in the cart was not found in your shop inventory.");
      }
      final stock = (prod['stock_quantity'] ?? 0) as int;
      if (stock < qty) {
        throw LocalApiError(400,
            "Insufficient stock for '${prod['name']}'. Available: $stock, Requested: $qty");
      }
      subtotal += price * qty - disc;
      lines.add({
        'product': pid,
        'product_name': prod['name'],
        'product_brand': prod['brand'],
        'quantity': qty,
        'unit_price': price,
        'discount': disc,
        'total_price': price * qty - disc,
        'imei_numbers': (it['imei'] ?? it['imei_numbers'] ?? '').toString(),
        'warranty_months': (prod['warranty_months'] ?? 0) as int,
        'purchase_price': _d(prod['purchase_price']),
      });
    }

    final discount = _d(payload['discount']);
    final tax = _d(payload['tax']);
    final total = (subtotal - discount) + tax;
    var paid = paymentMethod == 'CREDIT' ? 0.0 : _d(payload['paid_amount']);
    if (paid == 0 && paymentMethod != 'CREDIT') paid = total;
    if (paid > total) paid = total;
    final due = total - paid;

    final saleId = await AppLocalDb.txn((t) async {
      final prof = await t.query('shop_profile', where: 'id = ?', whereArgs: [1]);
      if (prof.isEmpty) {
        throw LocalApiError(400, 'Set up your shop profile first.');
      }
      final prefix = (prof.first['invoice_prefix'] ?? 'SZ-') as String;
      var next = (prof.first['next_invoice_number'] ?? 1001) as int;
      String invoiceNo;
      // Skip any number already used (safety for restored backups).
      while (true) {
        invoiceNo = '$prefix$next';
        final clash = await t.rawQuery(
            'SELECT id FROM sales WHERE invoice_number = ?', [invoiceNo]);
        if (clash.isEmpty) break;
        next++;
      }
      await t.update('shop_profile', {'next_invoice_number': next + 1},
          where: 'id = ?', whereArgs: [1]);

      final sid = await t.insert('sales', {
        'invoice_number': invoiceNo,
        'client_request_id': clientRequestId.isEmpty ? null : clientRequestId,
        'customer_id': customerId,
        'customer_name': customerName,
        'subtotal': subtotal,
        'discount': discount,
        'tax_amount': tax,
        'total_amount': total,
        'paid_amount': paid,
        'due_amount': due,
        'payment_status': due <= 0.009
            ? 'PAID'
            : (paid > 0 ? 'PARTIAL' : 'UNPAID'),
        'payment_method': paymentMethod,
        'notes': (payload['notes'] ?? '').toString(),
        'sale_date': AppLocalDb.nowIso(),
        'items_json': jsonEncode(lines),
      });

      for (final line in lines) {
        final pid = line['product'] as int;
        final qty = line['quantity'] as int;
        final rows = await t.query('products', where: 'id = ?', whereArgs: [pid]);
        if (rows.isEmpty) continue;
        final old = (rows.first['stock_quantity'] ?? 0) as int;
        await t.update('products', {'stock_quantity': old - qty},
            where: 'id = ?', whereArgs: [pid]);
        await t.insert('stock_movements', {
          'product_id': pid,
          'product_name': line['product_name'],
          'movement_type': 'SALE',
          'quantity': qty,
          'previous_stock': old,
          'new_stock': old - qty,
          'notes': 'Sold to $customerName (Bill #$invoiceNo)',
          'reference_id': invoiceNo,
          'moved_at': AppLocalDb.nowIso(),
        });
        final imei = line['imei_numbers'].toString();
        if (imei.isNotEmpty) {
          await t.rawUpdate(
              "UPDATE devices SET status = 'SOLD', sale_invoice = ? WHERE imei_1 = ? OR imei_2 = ?",
              [invoiceNo, imei, imei]);
        }
      }

      if (paid > 0) {
        await t.insert('payments', {
          'type': 'CUSTOMER_PAYMENT',
          'customer_id': customerId,
          'customer_name': customerName,
          'sale_invoice': invoiceNo,
          'amount': paid,
          'method': paymentMethod == 'CREDIT' ? 'CASH' : paymentMethod,
          'note': 'Payment received for invoice #$invoiceNo',
          'paid_at': AppLocalDb.nowIso(),
        });
      }
      return sid;
    });

    final sale = await AppLocalDb.q1('SELECT * FROM sales WHERE id = ?', [saleId]);
    return _checkoutResponse(sale!);
  }

  Map<String, dynamic> _checkoutResponse(Map<String, dynamic> sale) {
    final s = _saleJson(sale);
    // Same invoice text the server used to send to WhatsApp.
    final phone = (s['customer_phone'] ?? '').toString().replaceAll(RegExp(r'[^0-9]'), '');
    final msg = 'Namaste ${s['customer_name']},\n\n'
        'Here is your invoice *#${s['invoice_number']}*:\n'
        'Total: *₹${s['total_amount']}*\n'
        'Paid: *₹${s['paid_amount']}*\n'
        'Date: ${(s['sale_date'] as String).substring(0, 10)}\n\n'
        'Thank you for shopping with us!';
    return {
      'message': 'Sale completed successfully!',
      'sale': s,
      'whatsapp_share_url':
          'https://wa.me/$phone?text=${Uri.encodeComponent(msg)}',
    };
  }

  // ================= SALES =================
  Map<String, dynamic> _saleJson(Map<String, dynamic> r) {
    final items = jsonDecode(r['items_json'] as String) as List<dynamic>;
    double profit = 0;
    for (final it in items.cast<Map<String, dynamic>>()) {
      profit +=
          (_d(it['unit_price']) - _d(it['purchase_price'])) * _d(it['quantity']) -
              _d(it['discount']);
    }
    return {
      'id': r['id'],
      'customer': r['customer_id'],
      'customer_name': r['customer_name'],
      'customer_phone': '',
      'invoice_number': r['invoice_number'],
      'subtotal': _d(r['subtotal']),
      'discount': _d(r['discount']),
      'tax_amount': _d(r['tax_amount']),
      'total_amount': _d(r['total_amount']),
      'paid_amount': _d(r['paid_amount']),
      'due_amount': _d(r['due_amount']),
      'payment_status': r['payment_status'],
      'payment_status_display': r['payment_status'],
      'payment_method': r['payment_method'],
      'payment_method_display': r['payment_method'],
      'sale_date': r['sale_date'],
      'notes': r['notes'],
      'items': items,
      'gross_profit': profit,
      'created_at': r['sale_date'],
    };
  }

  Future<Map<String, dynamic>> _saleList(Map<String, dynamic> q) async {
    var sql = 'SELECT * FROM sales WHERE 1=1';
    final args = <Object?>[];
    final status = (q['status'] ?? '').toString();
    final search = (q['search'] ?? '').toString();
    final start = (q['start_date'] ?? '').toString();
    final end = (q['end_date'] ?? '').toString();
    if (status == 'DUE') {
      sql += ' AND due_amount > 0.009';
    } else if (status == 'PAID') {
      sql += ' AND due_amount <= 0.009';
    } else if (status.isNotEmpty) {
      sql += ' AND payment_status = ?';
      args.add(status);
    }
    if (search.isNotEmpty) {
      sql += ' AND (invoice_number LIKE ? OR customer_name LIKE ?)';
      args.add('%$search%');
      args.add('%$search%');
    }
    if (start.isNotEmpty) {
      sql += ' AND sale_date >= ?';
      args.add(start);
    }
    if (end.isNotEmpty) {
      sql += ' AND sale_date < ?';
      args.add(end);
    }
    sql += ' ORDER BY id DESC LIMIT 200';
    final rows = await AppLocalDb.q(sql, args);
    return {'results': rows.map(_saleJson).toList()};
  }

  Future<Map<String, dynamic>> _saleDetail(int id) async {
    final row = await AppLocalDb.q1('SELECT * FROM sales WHERE id = ?', [id]);
    if (row == null) throw LocalApiError(404, 'Sale not found.');
    return _saleJson(row);
  }

  // ================= DASHBOARD =================
  static String _dayStartIso([DateTime? base]) {
    final d = (base ?? DateTime.now());
    return DateTime(d.year, d.month, d.day).toIso8601String();
  }

  static (String, String) _rangeFor(String period) {
    final now = DateTime.now();
    switch (period) {
      case 'today':
        return (_dayStartIso(now), AppLocalDb.nowIso());
      case 'yesterday':
        final y = now.subtract(const Duration(days: 1));
        return (_dayStartIso(y), _dayStartIso(now));
      case '7d':
      case 'this_week':
        return (_dayStartIso(now.subtract(const Duration(days: 7))), AppLocalDb.nowIso());
      case '30d':
      case 'this_month':
        return (_dayStartIso(DateTime(now.year, now.month, 1)), AppLocalDb.nowIso());
      case 'last_month':
        final first = DateTime(now.year, now.month, 1);
        return (_dayStartIso(DateTime(now.year, now.month - 1, 1)), _dayStartIso(first));
      default:
        return (_dayStartIso(DateTime(now.year, now.month, 1)), AppLocalDb.nowIso());
    }
  }

  Future<Map<String, dynamic>> _dashboard() async {
    final todayStart = _dayStartIso();
    final salesAgg = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(total_amount),0) AS t, COALESCE(SUM(paid_amount),0) AS p, COUNT(*) AS c '
        'FROM sales WHERE sale_date >= ?', [todayStart]);
    final todaySales = _d(salesAgg?['t']);
    final todayCount = (salesAgg?['c'] ?? 0) as int;

    // Gross profit today: needs per-line cost, stored in items_json.
    final todaySalesRows = await AppLocalDb
        .q('SELECT items_json FROM sales WHERE sale_date >= ?', [todayStart]);
    double gross = 0;
    for (final row in todaySalesRows) {
      for (final it in jsonDecode(row['items_json'] as String)
          as List<dynamic>) {
        final m = it as Map<String, dynamic>;
        gross += (_d(m['unit_price']) - _d(m['purchase_price'])) *
                _d(m['quantity']) -
            _d(m['discount']);
      }
    }
    final expAgg = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(amount),0) AS s FROM expenses WHERE expense_date >= ?',
        [todayStart]);
    final todayExpenses = _d(expAgg?['s']);

    final dueAgg = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(due_amount),0) AS d FROM sales');
    final khataDue = _d(dueAgg?['d']);

    final supPayAgg = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(total_amount),0) AS t FROM purchases');
    final supPaidAgg = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(amount),0) AS s FROM payments WHERE supplier_id IS NOT NULL');
    final lowStock = await AppLocalDb.q(
        'SELECT name, stock_quantity, low_stock_threshold FROM products WHERE is_active = 1 AND stock_quantity <= low_stock_threshold ORDER BY stock_quantity ASC LIMIT 10');

    // 7-day trend
    final trend = <Map<String, dynamic>>[];
    for (int i = 6; i >= 0; i--) {
      final day = DateTime.now().subtract(Duration(days: i));
      final s = _dayStartIso(day);
      final e = _dayStartIso(day.add(const Duration(days: 1)));
      final sa = await AppLocalDb.q1(
          'SELECT COALESCE(SUM(total_amount),0) AS t FROM sales WHERE sale_date >= ? AND sale_date < ?',
          [s, e]);
      final ea = await AppLocalDb.q1(
          'SELECT COALESCE(SUM(amount),0) AS s FROM expenses WHERE expense_date >= ? AND expense_date < ?',
          [s, e]);
      trend.add({
        'day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][day.weekday - 1],
        'sales': _d(sa?['t']),
        'expenses': _d(ea?['s']),
      });
    }

    return {
      'today_sales': todaySales,
      'today_sales_count': todayCount,
      'today_gross_profit': gross,
      'today_expenses': todayExpenses,
      'today_net_profit': gross - todayExpenses,
      'khata_due': khataDue,
      'supplier_payable': _d(supPayAgg?['t']) - _d(supPaidAgg?['s']),
      'trend': trend,
      'low_stock': lowStock.map((r) => {
            'name': r['name'],
            'stock_quantity': r['stock_quantity'],
            'min_stock': r['low_stock_threshold'],
          }).toList(),
    };
  }

  // ================= REPORTS =================
  Future<Map<String, dynamic>> _profitLoss(Map<String, dynamic> q) async {
    final period = (q['period'] ?? 'this_month').toString();
    final (start, end) = _rangeFor(period);
    final rows = await AppLocalDb
        .q('SELECT items_json, total_amount, discount FROM sales WHERE sale_date >= ? AND sale_date < ?', [start, end]);
    double revenue = 0, cogs = 0;
    for (final r in rows) {
      revenue += _d(r['total_amount']);
      for (final it in jsonDecode(r['items_json'] as String) as List<dynamic>) {
        final m = it as Map<String, dynamic>;
        cogs += _d(m['purchase_price']) * _d(m['quantity']);
      }
    }
    final exp = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(amount),0) AS s FROM expenses WHERE expense_date >= ? AND expense_date < ?',
        [start, end]);
    final expenses = _d(exp?['s']);
    return {
      'period': period,
      'revenue': revenue,
      'cogs': cogs,
      'gross_profit': revenue - cogs,
      'expenses': expenses,
      'net_profit': revenue - cogs - expenses,
    };
  }

  Future<Map<String, dynamic>> _salesReport(Map<String, dynamic> q) async {
    final period = (q['period'] ?? 'this_month').toString();
    final (start, end) = _rangeFor(period);
    final rows = await AppLocalDb.q(
        'SELECT * FROM sales WHERE sale_date >= ? AND sale_date < ? ORDER BY sale_date ASC', [start, end]);
    // Daily buckets
    final byDay = <String, Map<String, dynamic>>{};
    for (final r in rows) {
      final day = (r['sale_date'] as String).substring(0, 10);
      byDay.putIfAbsent(day, () => {'sales': 0.0, 'orders': 0, 'profit': 0.0});
      byDay[day]!['sales'] = _d(byDay[day]!['sales']) + _d(r['total_amount']);
      byDay[day]!['orders'] = ((byDay[day]!['orders'] ?? 0) as int) + 1;
      for (final it in jsonDecode(r['items_json'] as String) as List<dynamic>) {
        final m = it as Map<String, dynamic>;
        byDay[day]!['profit'] = _d(byDay[day]!['profit']) +
            (_d(m['unit_price']) - _d(m['purchase_price'])) * _d(m['quantity']) -
            _d(m['discount']);
      }
    }
    return {
      'period': period,
      'total_sales': rows.fold(0.0, (a, r) => a + _d(r['total_amount'])),
      'order_count': rows.length,
      'trend': byDay.entries
          .map((e) => {'date': e.key, ...e.value})
          .toList()
        ..sort((a, b) => (a['date'] as String).compareTo(b['date'] as String)),
    };
  }

  Future<Map<String, dynamic>> _stockReport() async {
    final rows = await AppLocalDb.q(
        'SELECT * FROM products WHERE is_active = 1 ORDER BY stock_quantity ASC');
    return {
      'results': rows.map((r) => {
            'name': r['name'],
            'brand': r['brand'],
            'category': r['category'],
            'stock_quantity': r['stock_quantity'],
            'low_stock_threshold': r['low_stock_threshold'],
            'selling_price': _d(r['selling_price']),
            'purchase_price': _d(r['purchase_price']),
            'stock_value': _d(r['selling_price']) * ((r['stock_quantity'] ?? 0) as int),
            'is_low_stock': ((r['stock_quantity'] ?? 0) as int) <= ((r['low_stock_threshold'] ?? 5) as int),
          }).toList()
    };
  }

  Future<Map<String, dynamic>> _khataReport() async {
    final rows = await AppLocalDb.q(
        'SELECT c.id, c.name, c.phone, '
        'COALESCE((SELECT SUM(total_amount) FROM sales WHERE customer_id = c.id),0) AS total, '
        'COALESCE((SELECT SUM(amount) FROM payments WHERE customer_id = c.id),0) AS paid '
        'FROM customers c');
    return {
      'results': rows.map((r) => {
            'name': r['name'],
            'phone': r['phone'],
            'total_sales': _d(r['total']),
            'total_paid': _d(r['paid']),
            'outstanding_due': _d(r['total']) - _d(r['paid']),
          }).where((r) => _d(r['outstanding_due']) > 0.009).toList()
    };
  }

  Future<Map<String, dynamic>> _expenseReport(Map<String, dynamic> q) async {
    final period = (q['period'] ?? 'this_month').toString();
    final (start, end) = _rangeFor(period);
    final rows = await AppLocalDb.q(
        'SELECT category, COALESCE(SUM(amount),0) AS total, COUNT(*) AS c '
        'FROM expenses WHERE expense_date >= ? AND expense_date < ? GROUP BY category',
        [start, end]);
    return {
      'period': period,
      'total': rows.fold(0.0, (a, r) => a + _d(r['total'])),
      'by_category': rows.map((r) => {
            'category': r['category'],
            'total': _d(r['total']),
            'count': r['c'],
          }).toList()
    };
  }

  Future<Map<String, dynamic>> _gstReport(Map<String, dynamic> q) async {
    final period = (q['period'] ?? 'this_month').toString();
    final (start, end) = _rangeFor(period);
    final agg = await AppLocalDb.q1(
        'SELECT COALESCE(SUM(tax_amount),0) AS gst, COALESCE(SUM(total_amount),0) AS t, COUNT(*) AS c '
        'FROM sales WHERE sale_date >= ? AND sale_date < ?', [start, end]);
    return {
      'period': period,
      'total_gst': _d(agg?['gst']),
      'total_sales': _d(agg?['t']),
      'invoice_count': (agg?['c'] ?? 0) as int,
    };
  }

  Future<Map<String, dynamic>> _topProducts(Map<String, dynamic> q) async {
    final period = (q['period'] ?? 'this_month').toString();
    final (start, end) = _rangeFor(period);
    final rows = await AppLocalDb.q(
        'SELECT items_json FROM sales WHERE sale_date >= ? AND sale_date < ?', [start, end]);
    final agg = <String, Map<String, dynamic>>{};
    for (final r in rows) {
      for (final it in jsonDecode(r['items_json'] as String) as List<dynamic>) {
        final m = it as Map<String, dynamic>;
        final key = m['product_name'] as String;
        final e = agg.putIfAbsent(
            key,
            () => {'name': key, 'revenue': 0.0, 'units': 0, 'profit': 0.0});
        e['revenue'] = _d(e['revenue']) + _d(m['total_price']);
        e['units'] = ((e['units'] ?? 0) as int) + (_d(m['quantity']).round());
        e['profit'] = _d(e['profit']) +
            (_d(m['unit_price']) - _d(m['purchase_price'])) * _d(m['quantity']) -
            _d(m['discount']);
      }
    }
    final list = agg.values.toList()
      ..sort((a, b) => _d(b['revenue']).compareTo(_d(a['revenue'])));
    return {'results': list.take(10).toList()};
  }

  Future<Map<String, dynamic>> _topCustomers(Map<String, dynamic> q) async {
    final period = (q['period'] ?? 'this_month').toString();
    final (start, end) = _rangeFor(period);
    final rows = await AppLocalDb.q(
        'SELECT customer_name, SUM(total_amount) AS t, COUNT(*) AS c '
        'FROM sales WHERE sale_date >= ? AND sale_date < ? GROUP BY customer_name ORDER BY t DESC LIMIT 10',
        [start, end]);
    return {
      'results': rows.map((r) => {
            'name': r['customer_name'],
            'total_spend': _d(r['t']),
            'visits': r['c'],
          }).toList()
    };
  }

  // ================= SUBSCRIPTION: lifetime, local =================
  Map<String, dynamic> _subscriptionStatus() => {
        'plan_name': 'ShopZen Local — Lifetime',
        'price': 0,
        'price_display': 'Free forever on this device',
        'is_active': true,
        'status': 'ACTIVE',
        'start_date': '',
        'end_date': '',
        'days_remaining': 99999,
        'features': const [
          'Unlimited Products & Inventory',
          'Unlimited Customers & Digital Khata',
          'Lightning Fast POS Counter Billing',
          'Dual IMEI & Serial Tracker',
          '1-Click WhatsApp Reminders (Zero API fee)',
          'GST Ready Invoices & Thermal Print',
          'Supplier Purchases & Expense Tracking',
          'True Gross & Net Profit Analytics',
          'Local Backup & Restore',
          'Works Fully Offline — No Server Needed',
        ],
      };
}

/// Mimics the tiny slice of the Dio response the app reads:
/// `res.statusCode` and `res.data`.
class LocalResponse {
  final int statusCode;
  final Map<String, dynamic> data;
  LocalResponse(this.statusCode, this.data);
}

/// Carries an error status + clean message just like the server did.
class LocalApiError implements Exception {
  final int statusCode;
  final String message;
  const LocalApiError(this.statusCode, this.message);

  @override
  String toString() => 'LocalApiError($statusCode): $message';
}
