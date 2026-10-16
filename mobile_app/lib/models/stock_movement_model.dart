class StockMovementModel {
  final int id;
  final int? productId;
  final String productName;
  final int? deviceId;
  final String? deviceImei;
  final String movementType;
  final String movementTypeDisplay;
  final int quantity;
  final int previousStock;
  final int newStock;
  final String? notes;
  final String? referenceId;
  final String createdAt;

  StockMovementModel({
    required this.id,
    this.productId,
    required this.productName,
    this.deviceId,
    this.deviceImei,
    required this.movementType,
    required this.movementTypeDisplay,
    required this.quantity,
    required this.previousStock,
    required this.newStock,
    this.notes,
    this.referenceId,
    required this.createdAt,
  });

  factory StockMovementModel.fromJson(Map<String, dynamic> json) {
    return StockMovementModel(
      id: json['id'] ?? 0,
      productId: json['product'],
      productName: json['product_name'] ?? '',
      deviceId: json['device'],
      deviceImei: json['device_imei'],
      movementType: json['movement_type'] ?? '',
      movementTypeDisplay: json['movement_type_display'] ?? '',
      quantity: json['quantity'] ?? 0,
      previousStock: json['previous_stock'] ?? 0,
      newStock: json['new_stock'] ?? 0,
      notes: json['notes'],
      referenceId: json['reference_id'],
      createdAt: json['created_at'] ?? '',
    );
  }
}

/// One event on an IMEI-tracked unit's timeline (Phase 11). Everything on
/// it comes straight from the server; the app never invents entries.
class DeviceHistoryEntry {
  final String type;
  final String typeDisplay;
  final String? date;
  final String? reference;
  final String? note;

  DeviceHistoryEntry({
    required this.type,
    required this.typeDisplay,
    this.date,
    this.reference,
    this.note,
  });

  factory DeviceHistoryEntry.fromJson(Map<String, dynamic> json) {
    final raw = json['date'];
    return DeviceHistoryEntry(
      type: json['type'] ?? '',
      typeDisplay: json['type_display'] ?? '',
      date: raw?.toString(),
      reference: json['reference'],
      note: json['note'],
    );
  }

  /// True when the timeline marks this unit as sold.
  bool get isSale => type == 'SALE';
}
