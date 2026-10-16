"""Phase 8 — Backup & Restore for a single shop's data.

Export:  GET  /api/backup/          -> full shop dataset as downloadable JSON
Restore: POST /api/backup/restore/  -> validated, idempotent, dry-run capable import

Design rules (from the ShopZen master plan):
  * Tenant isolation is absolute: restored rows are ALWAYS attached to the
    authenticated request.business. Any business identifier inside the
    backup file is informational only and is never trusted.
  * Financial totals are never trusted from the file. Sale subtotals and
    totals, purchase totals, dues and payment statuses are recomputed
    server-side from the line items before a row is written.
  * Restore is idempotent: rows matched by their natural keys are skipped,
    never duplicated. Restoring the same backup twice is a no-op.
  * A restore either fully succeeds or fully fails (transaction.atomic).
  * Overpayment (paid > recomputed total) rejects the whole backup.
  * Only the business OWNER may export or restore.
  * No secrets, tokens, passwords or user credentials are ever exported.
  * Historical timestamps (created_at) are preserved exactly.
"""
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.timezone import is_aware, make_aware
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import HasActiveBusiness, OwnerOnly
from customers.models import Customer
from expenses.models import Expense, ExpenseCategory
from inventory.models import MobileDevice, StockMovement
from payments.models import Payment
from products.models import Category, Product
from purchases.models import Purchase, PurchaseItem
from reminders.models import ReminderLog, ReminderSetting
from sales.models import Sale, SaleItem
from suppliers.models import Supplier

BACKUP_VERSION = 1

# Business fields that are safe and meaningful to carry over in a backup.
# Owner, plan/subscription lifecycle and the logo binary are deliberately
# excluded (server-managed or not serializable).
BACKUP_BUSINESS_FIELDS = [
    'name', 'owner_name', 'phone', 'email', 'address', 'city', 'state',
    'pincode', 'gstin', 'upi_id', 'invoice_prefix', 'invoice_footer',
    'next_invoice_number',
]


def _dec(value, field, errors):
    """Parse a decimal from a backup value, recording errors by field."""
    if value is None or value == '':
        return Decimal('0.00')
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"Invalid decimal for '{field}': {value!r}")
        return None


def _dt(value, field, errors):
    """Parse an ISO datetime/date; None is acceptable (nullable fields)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if is_aware(value) else make_aware(value)
    parsed = parse_datetime(str(value)) or parse_date(str(value))
    if parsed is None:
        errors.append(f"Invalid date for '{field}': {value!r}")
        return None
    if isinstance(parsed, datetime) and not is_aware(parsed):
        parsed = make_aware(parsed)
    return parsed


def _money(value):
    return str(Decimal(value).quantize(Decimal('0.01'))) if value is not None else '0.00'


class BackupExportAPIView(APIView):
    """Download the authenticated shop's complete dataset as JSON."""
    permission_classes = [IsAuthenticated, HasActiveBusiness, OwnerOnly]

    def get(self, request):
        business = request.business
        data = _serialize_business(business)
        payload = {
            'meta': {
                'app': 'ShopZen',
                'backup_version': BACKUP_VERSION,
                'created_at': datetime.now().astimezone().isoformat(),
                'business_name': business.name,
                'record_counts': {k: len(v) for k, v in data.items()
                                  if isinstance(v, list)},
            },
            **data,
        }
        filename = (f"shopzen-backup-"
                    f"{business.name.replace(' ', '_')}-{datetime.now():%Y%m%d%H%M%S}.json")
        response = Response(payload)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Content-Type'] = 'application/json'
        return response


class BackupRestoreAPIView(APIView):
    """Import a previously exported ShopZen backup into this shop.

    POST body: the backup JSON object, optionally with a top-level
    ``"dry_run": true`` flag to validate and preview without writing.
    """
    permission_classes = [IsAuthenticated, HasActiveBusiness, OwnerOnly]

    def post(self, request):
        business = request.business
        data = request.data
        if not isinstance(data, dict):
            raise ValidationError({'detail': 'Backup must be a JSON object.'})
        if 'backup_version' not in (data.get('meta') or {}):
            raise ValidationError({'detail': 'Backup file is missing its version header.'})
        version = (data.get('meta') or {}).get('backup_version')
        if version != BACKUP_VERSION:
            raise ValidationError({
                'detail': (f'Unsupported backup version {version!r}. '
                           f'This server understands version {BACKUP_VERSION}.'),
            })

        plan = _ImportPlan(business)
        try:
            plan.run(data)
        except ValidationError:
            raise
        except Exception as exc:  # unexpected shape -> structured 400
            raise ValidationError({'detail': f'Backup could not be processed: {exc}'})

        # run() wrote everything inside one transaction (rolled back on any
        # failure); the dry_run flag is honoured there.
        dry_run = bool(data.get('dry_run', False))
        return Response(plan.report(dry_run=dry_run), status=status.HTTP_200_OK)


def _serialize_business(business):
    """Build the backup body (everything except the meta header)."""
    customers = list(Customer.objects.filter(business=business).order_by('pk'))
    suppliers = list(Supplier.objects.filter(business=business).order_by('pk'))
    products = list(Product.objects.filter(business=business).order_by('pk')
                    .select_related('category', 'supplier'))
    purchases = list(Purchase.objects.filter(business=business).order_by('pk')
                     .select_related('supplier').prefetch_related('items'))
    sales = list(Sale.objects.filter(business=business).order_by('pk')
                 .select_related('customer').prefetch_related('items'))
    expenses = list(Expense.objects.filter(business=business).order_by('pk')
                    .select_related('category'))
    payments = list(Payment.objects.filter(business=business).order_by('pk'))
    devices = list(MobileDevice.objects.filter(business=business).order_by('pk')
                   .select_related('product', 'customer'))
    movements = list(StockMovement.objects.filter(business=business).order_by('pk')
                     .select_related('product'))
    logs = list(ReminderLog.objects.filter(business=business).order_by('pk')
                .select_related('customer', 'sale'))

    return {
        'business': {f: getattr(business, f) for f in BACKUP_BUSINESS_FIELDS},
        'categories': [
            {'name': c.name, 'description': c.description,
             'created_at': c.created_at.isoformat()}
            for c in Category.objects.filter(business=business).order_by('pk')
        ],
        'expense_categories': [
            {'name': c.name, 'created_at': c.created_at.isoformat()}
            for c in ExpenseCategory.objects.filter(business=business).order_by('pk')
        ],
        'suppliers': [
            {
                'name': s.name, 'company_name': s.company_name, 'phone': s.phone,
                'email': s.email, 'address': s.address, 'gstin': s.gstin,
                'notes': s.notes, 'created_at': s.created_at.isoformat(),
            } for s in suppliers
        ],
        'customers': [
            {
                'name': c.name, 'phone': c.phone, 'email': c.email,
                'address': c.address, 'notes': c.notes,
                'credit_limit': _money(c.credit_limit),
                'created_at': c.created_at.isoformat(),
            } for c in customers
        ],
        'products': [
            {
                'name': p.name, 'brand': p.brand, 'sku': p.sku, 'barcode': p.barcode,
                'category_name': p.category.name if p.category else None,
                'supplier_company': p.supplier.company_name if p.supplier else None,
                'purchase_price': _money(p.purchase_price),
                'selling_price': _money(p.selling_price),
                'stock_quantity': p.stock_quantity, 'min_stock': p.min_stock,
                'warranty_months': p.warranty_months, 'is_imei_tracked': p.is_imei_tracked,
                'description': p.description, 'created_at': p.created_at.isoformat(),
            } for p in products
        ],
        'purchases': [
            {
                'supplier_company': p.supplier.company_name if p.supplier else None,
                'invoice_number': p.invoice_number,
                'purchase_date': p.purchase_date.isoformat() if p.purchase_date else None,
                'total_amount': _money(p.total_amount), 'paid_amount': _money(p.paid_amount),
                'payment_method': p.payment_method, 'notes': p.notes,
                'created_at': p.created_at.isoformat(),
                'items': [
                    {
                        'product_sku': i.product.sku, 'product_name': i.product.name,
                        'quantity': i.quantity, 'unit_cost': _money(i.unit_cost),
                    } for i in p.items.all()
                ],
            } for p in purchases
        ],
        'sales': [
            {
                'customer_phone': s.customer.phone if s.customer else None,
                'customer_name': s.customer.name if s.customer else None,
                'invoice_number': s.invoice_number,
                'sale_date': s.sale_date.isoformat() if s.sale_date else None,
                'discount': _money(s.discount), 'tax_amount': _money(s.tax_amount),
                'paid_amount': _money(s.paid_amount),
                'payment_method': s.payment_method, 'notes': s.notes,
                'created_at': s.created_at.isoformat(),
                'items': [
                    {
                        'product_sku': i.product.sku, 'product_name': i.product.name,
                        'quantity': i.quantity, 'unit_price': _money(i.unit_price),
                        'discount': _money(i.discount), 'imei_numbers': i.imei_numbers,
                    } for i in s.items.all().order_by('pk')
                ],
            } for s in sales
        ],
        'expenses': [
            {
                'category_name': e.category.name if e.category else None,
                'title': e.title, 'amount': _money(e.amount),
                'payment_method': e.payment_method,
                'expense_date': e.expense_date.isoformat() if e.expense_date else None,
                'notes': e.notes, 'created_at': e.created_at.isoformat(),
            } for e in expenses
        ],
        'payments': [
            {
                'payment_type': p.payment_type,
                'customer_phone': p.customer.phone if p.customer else None,
                'customer_name': p.customer.name if p.customer else None,
                'supplier_company': p.supplier.company_name if p.supplier else None,
                'sale_invoice_number': p.sale.invoice_number if p.sale else None,
                'purchase_invoice_number': p.purchase.invoice_number if p.purchase else None,
                'amount': _money(p.amount), 'payment_method': p.payment_method,
                'payment_date': p.payment_date.isoformat() if p.payment_date else None,
                'reference_number': p.reference_number, 'notes': p.notes,
                'created_at': p.created_at.isoformat(),
            } for p in payments
        ],
        'mobile_devices': [
            {
                'imei_1': d.imei_1, 'imei_2': d.imei_2, 'serial_number': d.serial_number,
                'model_name': d.model_name, 'brand': d.brand,
                'product_sku': d.product.sku if d.product else None,
                'product_name': d.product.name if d.product else None,
                'purchase_price': _money(d.purchase_price),
                'selling_price': _money(d.selling_price),
                'status': d.status,
                'customer_phone': d.customer.phone if d.customer else None,
                'customer_name': d.customer.name if d.customer else None,
                'sale_date': d.sale_date.isoformat() if d.sale_date else None,
                'warranty_expiry_date': (d.warranty_expiry_date.isoformat()
                                         if d.warranty_expiry_date else None),
                'notes': d.notes, 'created_at': d.created_at.isoformat(),
            } for d in devices
        ],
        'stock_movements': [
            {
                'product_sku': m.product.sku if m.product else None,
                'product_name': m.product.name if m.product else None,
                'device_imei': m.device.imei_1 if m.device else None,
                'movement_type': m.movement_type, 'quantity': m.quantity,
                'previous_stock': m.previous_stock, 'new_stock': m.new_stock,
                'notes': m.notes, 'reference_id': m.reference_id,
                'created_at': m.created_at.isoformat(),
            } for m in movements
        ],
        'reminder_logs': [
            {
                'customer_phone': l.customer.phone if l.customer else None,
                'customer_name': l.customer.name if l.customer else None,
                'sale_invoice_number': l.sale.invoice_number if l.sale else None,
                'amount': _money(l.amount),
                'due_date': l.due_date.isoformat() if l.due_date else None,
                'channel': l.channel, 'reminder_status': l.reminder_status,
                'note': l.note, 'created_at': l.created_at.isoformat(),
            } for l in logs
        ],
        'reminder_settings': _serialize_reminder_settings(business),
    }


def _serialize_reminder_settings(business):
    obj = ReminderSetting.objects.filter(business=business).first()
    if obj is None:
        return None
    return {'credit_days': obj.credit_days, 'due_soon_days': obj.due_soon_days}


class _ImportPlan:
    """Validates and imports a backup into one shop.

    Every row is written eagerly, but all imports run inside a single
    ``transaction.atomic()`` block — a ValidationError aborts the whole
    import, so a bad backup can never leave partial rows behind.
    """

    def __init__(self, business):
        self.business = business
        self.errors = []
        self.warnings = []
        self.imported = defaultdict(int)
        self.skipped = defaultdict(int)
        self.adjusted = defaultdict(int)
        # Caches keyed by natural identifiers; they hold both rows created
        # during this import and pre-existing DB rows.
        self._categories = {}
        self._expense_categories = {}
        self._suppliers = {}            # (company_name, name) -> Supplier
        self._suppliers_by_company = {}  # company_name -> Supplier
        self._customers = {}            # (phone, name) -> Customer
        self._products = {}             # ('sku', sku) | ('name', name, brand)
        self._sales = {}                # invoice_number -> Sale
        self._purchases = {}            # (invoice_number, supplier_pk) -> Purchase
        self._devices_by_imei = {}      # imei_1 -> MobileDevice (Phase 11 movements)

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #
    def run(self, data):
        """Import everything. Runs inside a transaction so a validation
        failure (ValidationError) rolls every write back."""
        with transaction.atomic():
            b = self.business
            self._apply_business_settings(data.get('business', {}))
            for cat in data.get('categories', []):
                self._category(b, cat)
            for cat in data.get('expense_categories', []):
                self._expense_category(b, cat)
            for sup in data.get('suppliers', []):
                self._supplier(b, sup)
            for cust in data.get('customers', []):
                self._customer(b, cust)
            for prod in data.get('products', []):
                self._product(b, prod)
            for purch in data.get('purchases', []):
                self._purchase(b, purch)
            for sale in data.get('sales', []):
                self._sale(b, sale)
            for exp in data.get('expenses', []):
                self._expense(b, exp)
            for dev in data.get('mobile_devices', []):
                self._device(b, dev)
            for pay in data.get('payments', []):
                self._payment(b, pay)
            for mov in data.get('stock_movements', []):
                self._movement(b, mov)
            for log in data.get('reminder_logs', []):
                self._reminder_log(b, log)
            self._reminder_settings(b, data.get('reminder_settings'))

            if self.errors:
                raise ValidationError({'detail': 'Backup validation failed.',
                                       'errors': self.errors})
            if data.get('dry_run'):
                # Nothing may survive a dry run.
                transaction.set_rollback(True)

    def report(self, dry_run=False):
        return {
            'dry_run': dry_run,
            'backup_version': BACKUP_VERSION,
            'imported': dict(self.imported),
            'skipped': dict(self.skipped),
            'adjusted': dict(self.adjusted),
            'warnings': self.warnings,
            'errors': self.errors,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _finish(self, kind, instance, raw_created_at, existed):
        if existed:
            self.skipped[kind] += 1
        else:
            instance.save()
            self.imported[kind] += 1
            self._preserve_created_at(instance, raw_created_at)
        return instance

    def _preserve_created_at(self, instance, raw_created_at):
        """Restore the historical created_at that auto_now_add overwrote."""
        created = _dt(raw_created_at, 'created_at', self.errors)
        if created is not None:
            # queryset.update() bypasses save(), keeping the auto-managed
            # updated_at out of its way.
            instance.__class__.objects.filter(pk=instance.pk).update(
                created_at=created)
            instance.created_at = created

    def _index_supplier(self, instance):
        self._suppliers[(instance.company_name or '', instance.name or '')] = instance
        if instance.company_name:
            self._suppliers_by_company.setdefault(instance.company_name, instance)

    # ------------------------------------------------------------------ #
    # Business settings
    # ------------------------------------------------------------------ #
    def _apply_business_settings(self, settings):
        if not isinstance(settings, dict) or not settings:
            return
        changed = []
        for field in BACKUP_BUSINESS_FIELDS:
            value = settings.get(field)
            if value is None:
                continue
            if field == 'next_invoice_number':
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    self.errors.append(f"Invalid next_invoice_number: {value!r}")
                    continue
                # Never roll the counter backwards into used invoice numbers.
                value = max(value, self.business.next_invoice_number)
            if str(getattr(self.business, field) or '') != str(value):
                setattr(self.business, field, value)
                changed.append(field)
        if changed:
            self.business.save()
            self.imported['business_settings'] = len(changed)
        else:
            self.skipped['business_settings'] = 1

    # ------------------------------------------------------------------ #
    # Catalog & parties
    # ------------------------------------------------------------------ #
    def _category(self, b, raw):
        name = (raw.get('name') or '').strip()
        if not name:
            self.errors.append('A category is missing its name.')
            return None
        existing = self._categories.get(name)
        if existing is None:
            existing = Category.objects.filter(business=b, name=name).first()
        if existing is not None:
            self.skipped['categories'] += 1
            self._categories[name] = existing
            return existing
        instance = Category(business=b, name=name, description=raw.get('description'))
        self._finish('categories', instance, raw.get('created_at'), existed=False)
        self._categories[name] = instance
        return instance

    def _expense_category(self, b, raw):
        name = (raw.get('name') or '').strip()
        if not name:
            self.errors.append('An expense category is missing its name.')
            return None
        existing = self._expense_categories.get(name)
        if existing is None:
            existing = ExpenseCategory.objects.filter(business=b, name=name).first()
        if existing is not None:
            self.skipped['expense_categories'] += 1
            self._expense_categories[name] = existing
            return existing
        instance = ExpenseCategory(business=b, name=name)
        self._finish('expense_categories', instance, raw.get('created_at'), existed=False)
        self._expense_categories[name] = instance
        return instance

    def _supplier(self, b, raw):
        company = (raw.get('company_name') or '').strip()
        name = (raw.get('name') or '').strip()
        if not company and not name:
            self.errors.append('A supplier is missing both company and contact name.')
            return None
        key = (company, name)
        existing = self._suppliers.get(key)
        if existing is None:
            existing = Supplier.objects.filter(
                business=b, company_name=company, name=name).first()
        if existing is not None:
            self.skipped['suppliers'] += 1
            self._index_supplier(existing)
            return existing
        instance = Supplier(
            business=b, name=name, company_name=company, phone=raw.get('phone') or '',
            email=raw.get('email'), address=raw.get('address'),
            gstin=raw.get('gstin'), notes=raw.get('notes'),
        )
        self._finish('suppliers', instance, raw.get('created_at'), existed=False)
        self._index_supplier(instance)
        return instance

    def _customer(self, b, raw):
        name = (raw.get('name') or '').strip()
        phone = (raw.get('phone') or '').strip()
        if not name or not phone:
            self.errors.append(f"A customer is missing its name or phone: {raw!r}")
            return None
        key = (phone, name)
        existing = self._customers.get(key)
        if existing is None:
            existing = Customer.objects.filter(business=b, name=name, phone=phone).first()
        if existing is not None:
            self.skipped['customers'] += 1
            self._customers[key] = existing
            return existing
        limit = _dec(raw.get('credit_limit'), 'credit_limit', self.errors)
        instance = Customer(
            business=b, name=name, phone=phone, email=raw.get('email'),
            address=raw.get('address'), notes=raw.get('notes'),
            credit_limit=limit if limit is not None else Decimal('0.00'),
        )
        self._finish('customers', instance, raw.get('created_at'), existed=False)
        self._customers[key] = instance
        return instance

    def _product(self, b, raw):
        name = (raw.get('name') or '').strip()
        if not name:
            self.errors.append('A product is missing its name.')
            return None
        sku = (raw.get('sku') or '').strip() or None
        key = ('sku', sku) if sku else ('name', name, raw.get('brand'))
        existing = self._products.get(key)
        if existing is None:
            if sku:
                existing = Product.objects.filter(business=b, sku=sku).first()
            else:
                existing = Product.objects.filter(
                    business=b, name=name, brand=raw.get('brand') or None).first()
        if existing is not None:
            self.skipped['products'] += 1
            self._products[key] = existing
            return existing

        category_name = raw.get('category_name')
        category = self._categories.get(category_name) if category_name else None
        if category_name and category is None:
            # Category missing from the backup: restore under a new one
            # rather than dropping the product.
            category = self._category(b, {'name': category_name})

        supplier_company = raw.get('supplier_company')
        supplier = self._suppliers_by_company.get(supplier_company) \
            if supplier_company else None
        if supplier is None and supplier_company:
            self.warnings.append(
                f"Product '{name}' references supplier '{supplier_company}' that is "
                'not in this backup; the product imports without a supplier link.')

        purchase_price = _dec(raw.get('purchase_price'), 'purchase_price', self.errors)
        selling_price = _dec(raw.get('selling_price'), 'selling_price', self.errors)
        if purchase_price is None or selling_price is None:
            return None
        instance = Product(
            business=b, category=category, name=name, brand=raw.get('brand'),
            sku=sku, barcode=raw.get('barcode'),
            purchase_price=purchase_price, selling_price=selling_price,
            stock_quantity=int(raw.get('stock_quantity') or 0),
            min_stock=int(raw.get('min_stock') or 0),
            warranty_months=int(raw.get('warranty_months') or 0),
            is_imei_tracked=bool(raw.get('is_imei_tracked')),
            description=raw.get('description'),
        )
        self._finish('products', instance, raw.get('created_at'), existed=False)
        self._products[key] = instance
        return instance

    def _product_from_ref(self, raw_sku, raw_name):
        """Resolve a product reference from an item line."""
        sku = (raw_sku or '').strip() if raw_sku else None
        if sku:
            hit = self._products.get(('sku', sku))
            if hit is None:
                hit = Product.objects.filter(business=self.business, sku=sku).first()
                if hit is not None:
                    self._products[('sku', sku)] = hit
            if hit is not None:
                return hit
        name = (raw_name or '').strip()
        if name:
            hit = self._products.get(('name', name, None))
            if hit is None:
                hit = Product.objects.filter(business=self.business, name=name).first()
                if hit is not None:
                    self._products[('name', name, None)] = hit
            if hit is not None:
                return hit
        return None

    def _customer_from_ref(self, phone, name):
        hit = self._customers.get((phone, name))
        if hit is None and phone:
            hit = Customer.objects.filter(
                business=self.business, phone=phone, name=name).first()
            if hit is not None:
                self._customers[(phone, name)] = hit
        return hit

    def _supplier_from_ref(self, company):
        if not company:
            return None
        hit = self._suppliers_by_company.get(company)
        if hit is None:
            hit = Supplier.objects.filter(
                business=self.business, company_name=company).first()
            if hit is not None:
                self._index_supplier(hit)
        return hit

    # ------------------------------------------------------------------ #
    # Financial documents — totals recomputed server-side
    # ------------------------------------------------------------------ #
    def _purchase(self, b, raw):
        invoice_number = (raw.get('invoice_number') or '').strip()
        supplier = self._supplier_from_ref(raw.get('supplier_company'))
        if not invoice_number or supplier is None:
            self.warnings.append(
                f"Purchase skipped (missing invoice number or supplier): {raw!r}")
            self.skipped['purchases'] += 1
            return None
        existing = self._purchases.get((invoice_number, supplier.pk))
        if existing is None:
            existing = Purchase.objects.filter(
                business=b, invoice_number=invoice_number, supplier=supplier).first()
        if existing is not None:
            self.skipped['purchases'] += 1
            self._purchases[(invoice_number, supplier.pk)] = existing
            return existing

        line_total = Decimal('0.00')
        items = []
        for it in raw.get('items') or []:
            product = self._product_from_ref(it.get('product_sku'), it.get('product_name'))
            if product is None:
                self.warnings.append(
                    f"Purchase {invoice_number}: item skipped (product not found): {it!r}")
                continue
            unit_cost = _dec(it.get('unit_cost'), 'unit_cost', self.errors)
            if unit_cost is None:
                continue
            qty = int(it.get('quantity') or 1)
            line_total += unit_cost * Decimal(qty)
            staged = PurchaseItem(product=product, quantity=qty, unit_cost=unit_cost)
            # total_cost is derived in save(); stage it for validation only.
            staged.total_cost = unit_cost * Decimal(qty)
            items.append(staged)

        total_amount = line_total
        file_total = _dec(raw.get('total_amount'), 'total_amount', self.errors)
        paid_amount = _dec(raw.get('paid_amount'), 'paid_amount', self.errors)
        if paid_amount is None:
            return None
        if file_total is not None and file_total != total_amount:
            self.adjusted['purchases'] += 1
            self.warnings.append(
                f"Purchase {invoice_number}: file total {_money(file_total)} did not match "
                f"the sum of its items {_money(total_amount)}; the recomputed value is used.")
        if paid_amount > total_amount:
            self.errors.append(
                f"Purchase {invoice_number}: paid {_money(paid_amount)} exceeds the "
                f"recomputed total {_money(total_amount)} (overpayment not allowed).")
            return None

        purchase = Purchase(
            business=b, supplier=supplier, invoice_number=invoice_number,
            purchase_date=_dt(raw.get('purchase_date'), 'purchase_date', self.errors)
            or datetime.now().date(),
            total_amount=total_amount, paid_amount=paid_amount,
            payment_method=raw.get('payment_method') or 'CASH',
            notes=raw.get('notes'),
        )
        # Purchase.save() recomputes due_amount; set it for consistency.
        purchase.due_amount = max(Decimal('0.00'), total_amount - paid_amount)
        self._finish('purchases', purchase, raw.get('created_at'), existed=False)
        for item in items:
            item.purchase = purchase
            item.save()  # PurchaseItem.save() recomputes total_cost.
        self._purchases[(invoice_number, supplier.pk)] = purchase
        return purchase

    def _sale(self, b, raw):
        invoice_number = (raw.get('invoice_number') or '').strip()
        customer = self._customer_from_ref(
            raw.get('customer_phone'), raw.get('customer_name'))
        if not invoice_number:
            self.warnings.append(f"Sale skipped (missing invoice number): {raw!r}")
            self.skipped['sales'] += 1
            return None
        existing = self._sales.get(invoice_number)
        if existing is None:
            existing = Sale.objects.filter(
                business=b, invoice_number=invoice_number).first()
        if existing is not None:
            self.skipped['sales'] += 1
            self._sales[invoice_number] = existing
            return existing

        # Sales attach to a customer by design; a backup whose customer
        # cannot be resolved cannot be imported and is reported, not faked.
        if customer is None:
            self.warnings.append(
                f"Sale {invoice_number} skipped (customer not found in this "
                'backup and not already in the shop).')
            self.skipped['sales'] += 1
            return None

        line_subtotal = Decimal('0.00')
        items = []
        for it in raw.get('items') or []:
            product = self._product_from_ref(it.get('product_sku'), it.get('product_name'))
            if product is None:
                self.warnings.append(
                    f"Sale {invoice_number}: item skipped (product not found): {it!r}")
                continue
            unit_price = _dec(it.get('unit_price'), 'unit_price', self.errors)
            discount = _dec(it.get('discount'), 'discount', self.errors)
            if unit_price is None or discount is None:
                continue
            qty = int(it.get('quantity') or 1)
            line_subtotal += (unit_price * Decimal(qty)) - discount
            staged = SaleItem(
                product=product, quantity=qty, unit_price=unit_price, discount=discount,
                imei_numbers=it.get('imei_numbers'),
            )
            staged.total_price = max(Decimal('0.00'),
                                     (unit_price * Decimal(qty)) - discount)
            items.append(staged)

        discount = _dec(raw.get('discount'), 'discount', self.errors)
        tax_amount = _dec(raw.get('tax_amount'), 'tax_amount', self.errors)
        paid_amount = _dec(raw.get('paid_amount'), 'paid_amount', self.errors)
        if None in (discount, tax_amount, paid_amount):
            return None

        subtotal = line_subtotal
        total_amount = subtotal - discount + tax_amount
        file_total = _dec(raw.get('total_amount'), 'total_amount', self.errors)
        if file_total is not None and file_total != total_amount:
            self.adjusted['sales'] += 1
            self.warnings.append(
                f"Sale {invoice_number}: file total {_money(file_total)} did not match "
                f"the recomputed total {_money(total_amount)}; the recomputed value is used.")
        if paid_amount > total_amount:
            self.errors.append(
                f"Sale {invoice_number}: paid {_money(paid_amount)} exceeds the "
                f"recomputed total {_money(total_amount)} (overpayment not allowed).")
            return None

        sale_kwargs = dict(
            business=b, customer=customer, invoice_number=invoice_number,
            subtotal=subtotal, discount=discount, tax_amount=tax_amount,
            total_amount=total_amount, paid_amount=paid_amount,
            payment_method=raw.get('payment_method') or 'CASH',
            notes=raw.get('notes'),
        )
        sale_date = _dt(raw.get('sale_date'), 'sale_date', self.errors)
        if sale_date is not None:
            sale_kwargs['sale_date'] = sale_date

        sale = Sale(**sale_kwargs)
        # Sale.save() recomputes due_amount and payment_status from these
        # server-side totals — the file's values are never trusted.
        self._finish('sales', sale, raw.get('created_at'), existed=False)
        for item in items:
            item.sale = sale
            item.save()  # SaleItem.save() recomputes total_price.
        self._sales[invoice_number] = sale
        return sale

    # ------------------------------------------------------------------ #
    # Everything else
    # ------------------------------------------------------------------ #
    def _expense(self, b, raw):
        title = (raw.get('title') or '').strip()
        amount = _dec(raw.get('amount'), 'amount', self.errors)
        if not title or amount is None or amount < 0:
            self.warnings.append(f"Expense skipped (invalid): {raw!r}")
            self.skipped['expenses'] += 1
            return None
        expense_date = _dt(raw.get('expense_date'), 'expense_date', self.errors)
        expense_date = expense_date or datetime.now().date()
        existing = Expense.objects.filter(
            business=b, title=title, amount=amount, expense_date=expense_date).first()
        if existing is not None:
            self.skipped['expenses'] += 1
            return existing
        category_name = raw.get('category_name')
        category = self._expense_categories.get(category_name) if category_name else None
        instance = Expense(
            business=b, category=category, title=title, amount=amount,
            payment_method=raw.get('payment_method') or 'CASH',
            expense_date=expense_date, notes=raw.get('notes'),
        )
        self._finish('expenses', instance, raw.get('created_at'), existed=False)
        return instance

    def _device(self, b, raw):
        imei_1 = (raw.get('imei_1') or '').strip()
        product = self._product_from_ref(raw.get('product_sku'), raw.get('product_name'))
        if not imei_1:
            self.warnings.append('Device skipped (missing IMEI 1).')
            self.skipped['mobile_devices'] += 1
            return None
        existing = MobileDevice.objects.filter(business=b, imei_1=imei_1).first()
        if existing is not None:
            self._devices_by_imei[imei_1] = existing
            self.skipped['mobile_devices'] += 1
            return existing
        if product is None:
            self.warnings.append(
                f"Device {imei_1} skipped (product not found in backup or shop).")
            self.skipped['mobile_devices'] += 1
            return None
        purchase_price = _dec(raw.get('purchase_price'), 'purchase_price', self.errors)
        selling_price = _dec(raw.get('selling_price'), 'selling_price', self.errors)
        if purchase_price is None or selling_price is None:
            return None
        customer = self._customer_from_ref(
            raw.get('customer_phone'), raw.get('customer_name'))
        instance = MobileDevice(
            business=b, product=product, imei_1=imei_1, imei_2=raw.get('imei_2'),
            serial_number=raw.get('serial_number'), model_name=raw.get('model_name'),
            brand=raw.get('brand'), purchase_price=purchase_price,
            selling_price=selling_price, status=raw.get('status') or 'IN_STOCK',
            customer=customer,
            sale_date=_dt(raw.get('sale_date'), 'sale_date', self.errors),
            warranty_expiry_date=_dt(raw.get('warranty_expiry_date'),
                                     'warranty_expiry_date', self.errors),
            notes=raw.get('notes'),
        )
        self._finish('mobile_devices', instance, raw.get('created_at'), existed=False)
        self._devices_by_imei[imei_1] = instance
        return instance

    def _payment(self, b, raw):
        payment_type = (raw.get('payment_type') or '').strip()
        amount = _dec(raw.get('amount'), 'amount', self.errors)
        if amount is None or amount <= 0:
            self.warnings.append(f"Payment skipped (invalid amount): {raw!r}")
            self.skipped['payments'] += 1
            return None
        if payment_type not in ('CUSTOMER_PAYMENT', 'SUPPLIER_PAYMENT'):
            self.warnings.append(f"Payment skipped (unknown type {payment_type!r}).")
            self.skipped['payments'] += 1
            return None
        customer = self._customer_from_ref(
            raw.get('customer_phone'), raw.get('customer_name'))
        supplier = self._supplier_from_ref(raw.get('supplier_company'))
        payment_date = _dt(raw.get('payment_date'), 'payment_date', self.errors)
        payment_date = payment_date or datetime.now().date()
        lookup = dict(
            business=b, payment_type=payment_type, amount=amount,
            payment_date=payment_date, reference_number=raw.get('reference_number'),
        )
        if payment_type == 'CUSTOMER_PAYMENT':
            if customer is None:
                self.warnings.append(
                    f"Payment skipped (customer not resolvable): {raw!r}")
                self.skipped['payments'] += 1
                return None
            lookup['customer'] = customer
        else:
            if supplier is None:
                self.warnings.append(
                    f"Payment skipped (supplier not resolvable): {raw!r}")
                self.skipped['payments'] += 1
                return None
            lookup['supplier'] = supplier
        existing = Payment.objects.filter(**lookup).first()
        if existing is not None:
            self.skipped['payments'] += 1
            return existing
        instance = Payment(
            business=b, payment_type=payment_type, customer=customer, supplier=supplier,
            amount=amount, payment_method=raw.get('payment_method') or 'CASH',
            payment_date=payment_date,
            reference_number=raw.get('reference_number'), notes=raw.get('notes'),
        )
        # Optional links to the restored documents (both are saved by now,
        # so their primary keys are available).
        sale_invoice = raw.get('sale_invoice_number')
        purchase_invoice = raw.get('purchase_invoice_number')
        if sale_invoice and self._sales.get(sale_invoice) is not None:
            instance.sale = self._sales[sale_invoice]
        elif sale_invoice:
            instance.sale = Sale.objects.filter(
                business=b, invoice_number=sale_invoice).first()
        if purchase_invoice:
            match = next((p for (num, _sp), p in self._purchases.items()
                          if num == purchase_invoice), None)
            if match is None:
                match = Purchase.objects.filter(
                    business=b, invoice_number=purchase_invoice).first()
            instance.purchase = match

        self._finish('payments', instance, raw.get('created_at'), existed=False)
        return instance

    def _movement(self, b, raw):
        product = self._product_from_ref(raw.get('product_sku'), raw.get('product_name'))
        movement_type = (raw.get('movement_type') or '').strip()
        created = _dt(raw.get('created_at'), 'created_at', self.errors)
        if product is None or not movement_type or created is None:
            self.warnings.append(f"Stock movement skipped (invalid): {raw!r}")
            self.skipped['stock_movements'] += 1
            return None
        quantity = int(raw.get('quantity') or 0)
        previous_stock = int(raw.get('previous_stock') or 0)
        new_stock = int(raw.get('new_stock') or 0)
        existing = StockMovement.objects.filter(
            business=b, product=product, movement_type=movement_type,
            quantity=quantity, previous_stock=previous_stock, new_stock=new_stock,
            created_at=created).first()
        if existing is not None:
            self.skipped['stock_movements'] += 1
            return existing
        instance = StockMovement(
            business=b, product=product, movement_type=movement_type,
            quantity=quantity, previous_stock=previous_stock, new_stock=new_stock,
            notes=raw.get('notes'), reference_id=raw.get('reference_id'),
            device=self._device_by_imei.get((raw.get('device_imei') or '').strip())
            if raw.get('device_imei') else None,
        )
        self._finish('stock_movements', instance, created, existed=False)
        return instance

    def _reminder_log(self, b, raw):
        customer = self._customer_from_ref(
            raw.get('customer_phone'), raw.get('customer_name'))
        channel = (raw.get('channel') or '').strip()
        amount = _dec(raw.get('amount'), 'amount', self.errors)
        created = _dt(raw.get('created_at'), 'created_at', self.errors)
        if customer is None or not channel or amount is None or created is None:
            self.warnings.append(f"Reminder log skipped (invalid): {raw!r}")
            self.skipped['reminder_logs'] += 1
            return None
        existing = ReminderLog.objects.filter(
            business=b, customer=customer, amount=amount, channel=channel,
            created_at=created).first()
        if existing is not None:
            self.skipped['reminder_logs'] += 1
            return existing
        instance = ReminderLog(
            business=b, customer=customer, amount=amount, channel=channel,
            reminder_status=raw.get('reminder_status') or 'DUE',
            due_date=_dt(raw.get('due_date'), 'due_date', self.errors),
            note=raw.get('note') or '',
            sent_by=b.owner,
        )
        self._finish('reminder_logs', instance, created, existed=False)
        return instance

    def _reminder_settings(self, b, raw):
        if not isinstance(raw, dict) or not raw:
            return
        instance = ReminderSetting.objects.filter(business=b).first()
        credit_days = int(raw.get('credit_days') or 30)
        due_soon_days = int(raw.get('due_soon_days') or 7)
        if instance is None:
            instance = ReminderSetting(
                business=b, credit_days=credit_days, due_soon_days=due_soon_days)
            self._finish('reminder_settings', instance, None, existed=False)
        else:
            if (instance.credit_days, instance.due_soon_days) != (credit_days, due_soon_days):
                instance.credit_days = credit_days
                instance.due_soon_days = due_soon_days
                instance.save()
                self.imported['reminder_settings'] = 1
            else:
                self.skipped['reminder_settings'] = 1
