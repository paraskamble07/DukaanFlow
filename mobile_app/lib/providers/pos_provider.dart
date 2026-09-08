import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/constants/api_constants.dart';
import '../core/network/api_client.dart';
import '../core/network/local_dio.dart';
import '../models/product_model.dart';
import '../models/sale_model.dart';
import 'auth_provider.dart';

class CartItem {
  final ProductModel product;
  int quantity;
  double unitPrice;
  double discount;
  int? deviceId;
  String? imeiString;

  CartItem({
    required this.product,
    this.quantity = 1,
    required this.unitPrice,
    this.discount = 0.0,
    this.deviceId,
    this.imeiString,
  });

  double get total => ((unitPrice * quantity) - discount).clamp(0.0, double.infinity);
}

class PosState {
  final List<CartItem> items;
  final int? selectedCustomerId;
  final String? customerName;
  final String? customerPhone;
  final double extraDiscount;
  final double taxAmount;
  final double paidAmount;
  final String paymentMethod;
  final String notes;
  final bool isSubmitting;
  final String? error;

  PosState({
    this.items = const [],
    this.selectedCustomerId,
    this.customerName,
    this.customerPhone,
    this.extraDiscount = 0.0,
    this.taxAmount = 0.0,
    this.paidAmount = 0.0,
    this.paymentMethod = 'CASH',
    this.notes = '',
    this.isSubmitting = false,
    this.error,
  });

  double get subtotal => items.fold(0.0, (sum, i) => sum + i.total);
  double get grandTotal => ((subtotal - extraDiscount) + taxAmount).clamp(0.0, double.infinity);
  double get dueAmount => (grandTotal - paidAmount).clamp(0.0, double.infinity);

  PosState copyWith({
    List<CartItem>? items,
    int? selectedCustomerId,
    String? customerName,
    String? customerPhone,
    double? extraDiscount,
    double? taxAmount,
    double? paidAmount,
    String? paymentMethod,
    String? notes,
    bool? isSubmitting,
    String? error,
  }) {
    return PosState(
      items: items ?? this.items,
      selectedCustomerId: selectedCustomerId ?? this.selectedCustomerId,
      customerName: customerName ?? this.customerName,
      customerPhone: customerPhone ?? this.customerPhone,
      extraDiscount: extraDiscount ?? this.extraDiscount,
      taxAmount: taxAmount ?? this.taxAmount,
      paidAmount: paidAmount ?? this.paidAmount,
      paymentMethod: paymentMethod ?? this.paymentMethod,
      notes: notes ?? this.notes,
      isSubmitting: isSubmitting ?? this.isSubmitting,
      error: error,
    );
  }
}

class PosNotifier extends StateNotifier<PosState> {
  final ApiClient _client;

  PosNotifier(this._client) : super(PosState());

  void addToCart(ProductModel product, {int? deviceId, String? imei}) {
    final existingIndex = state.items.indexWhere(
      (item) => item.product.id == product.id && item.deviceId == null,
    );

    if (product.isImeiTracked) {
      // Must be individual tracked unit
      final updated = [...state.items, CartItem(
        product: product,
        quantity: 1,
        unitPrice: product.sellingPrice,
        deviceId: deviceId,
        imeiString: imei,
      )];
      state = state.copyWith(items: updated);
    } else {
      if (existingIndex > -1) {
        final current = state.items[existingIndex];
        if (current.quantity < product.stockQuantity) {
          current.quantity += 1;
          state = state.copyWith(items: [...state.items]);
        }
      } else {
        final updated = [...state.items, CartItem(
          product: product,
          quantity: 1,
          unitPrice: product.sellingPrice,
        )];
        state = state.copyWith(items: updated);
      }
    }
    // Auto-update paid amount if CASH
    if (state.paymentMethod != 'CREDIT') {
      state = state.copyWith(paidAmount: state.grandTotal);
    }
  }

  void updateQuantity(int index, int qty) {
    if (qty <= 0) {
      removeFromCart(index);
      return;
    }
    final items = [...state.items];
    items[index].quantity = qty;
    state = state.copyWith(items: items);
    if (state.paymentMethod != 'CREDIT') {
      state = state.copyWith(paidAmount: state.grandTotal);
    }
  }

  void updateItemDiscount(int index, double disc) {
    final items = [...state.items];
    items[index].discount = disc;
    state = state.copyWith(items: items);
  }

  void removeFromCart(int index) {
    final items = [...state.items]..removeAt(index);
    state = state.copyWith(items: items);
    if (state.paymentMethod != 'CREDIT') {
      state = state.copyWith(paidAmount: state.grandTotal);
    }
  }

  void setCustomer(int? id, String? name, String? phone) {
    state = state.copyWith(selectedCustomerId: id, customerName: name, customerPhone: phone);
  }

  void setPaymentMethod(String method) {
    state = state.copyWith(
      paymentMethod: method,
      paidAmount: method == 'CREDIT' ? 0.0 : state.grandTotal,
    );
  }

  void setPaidAmount(double amt) {
    state = state.copyWith(paidAmount: amt);
  }

  void setExtraDiscount(double disc) {
    state = state.copyWith(extraDiscount: disc);
  }

  void setTax(double tax) {
    state = state.copyWith(taxAmount: tax);
  }

  void clearCart() {
    state = PosState();
  }

  Future<Map<String, dynamic>?> checkout() async {
    if (state.items.isEmpty) return null;

    state = state.copyWith(isSubmitting: true, error: null);

    // Every checkout attempt carries one id: the server returns the same
    // sale for a replayed id, so double taps and sync retries can never
    // create a second copy of this bill.
    final payload = {
      'client_request_id':
          DateTime.now().microsecondsSinceEpoch.toString() +
              '-${state.items.length}-${state.selectedCustomerId ?? 'w'}',
      'customer_id': state.selectedCustomerId,
      'new_customer_name': state.customerName,
      'new_customer_phone': state.customerPhone,
      'payment_method': state.paymentMethod,
      'discount': state.extraDiscount,
      'tax': state.taxAmount,
      'paid_amount': state.paidAmount,
      'notes': state.notes,
      'items': state.items.map((i) => {
        'product_id': i.product.id,
        'quantity': i.quantity,
        'unit_price': i.unitPrice,
        'discount': i.discount,
        'device_id': i.deviceId,
      }).toList(),
    };

    try {
      final res = await _client.dio.post(ApiConstants.posCheckout, data: payload);
      if (res.statusCode == 201) {
        state = PosState();
        return res.data;
      }
      state = state.copyWith(
        isSubmitting: false,
        error: 'Checkout could not be completed. Please try again.',
      );
      return null;
    } on LocalApiError catch (e) {
      // Local database rejected the bill (stock, validation) — show the
      // clean message; nothing was saved.
      state = state.copyWith(isSubmitting: false, error: e.message);
      return null;
    } catch (e) {
      state = state.copyWith(
        isSubmitting: false,
        error: 'Checkout could not be completed: $e',
      );
      return null;
    }
  }
}

final posProvider = StateNotifierProvider<PosNotifier, PosState>((ref) {
  final client = ref.watch(apiClientProvider);
  return PosNotifier(client);
});
