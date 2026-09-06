# ShopZen REST API Documentation

Base URL: `https://dukaanflow.onrender.com/api/` (production) or `http://<LAN-IP>:8000/api/` (development)

Authentication: **JWT Bearer** — send `Authorization: Bearer <access_token>` on every request.
Tenant isolation is automatic: every endpoint derives the shop from the **authenticated user** — a `shop_id`/`business_id` parameter is never accepted from clients, so cross-shop access is impossible (verified by the `TenantIsolationTest` suite in `api/tests.py`).

Standard responses:
- Success: the resource object / list (paginated where large: `{"count": n, "next": url, "previous": url, "results": [...]}`)
- Error: `{"error": "Readable message"}` with status `400/401/403/404`

---

## 1. Authentication

### Register (creates owner + shop tenant)
`POST /api/auth/register/`
```json
{
  "full_name": "Vikas Patil",
  "shop_name": "Vikas Mobile Hub",
  "phone": "9811223344",
  "email": "vikas@example.com",
  "password": "Secret123"
}
```
→ `201` `{ tokens: {access, refresh}, user, business }`

### Login
`POST /api/auth/login/` with `{"email", "password"}`
→ `200` `{ tokens: {access, refresh}, user, business }`

### Refresh token
`POST /api/auth/refresh/` with `{"refresh": "<refresh token>"}` → `{"access": "..."}`

### Profile
`GET /api/auth/profile/` → `{ user, business }`
`PUT /api/auth/profile/` — update first_name/last_name/phone

### Business (shop) settings
`GET /api/business/settings/` · `PUT /api/business/settings/` (partial update: name, phone, address, gstin, invoice_prefix, logo …)

---

## 2. Dashboard
`GET /api/dashboard/`
```json
{
  "today": { "date", "sales", "sales_count", "gross_profit", "net_profit", "expenses" },
  "receivables": { "total_receivable", "total_payable" },
  "inventory": { "total_products", "low_stock_count", "low_stock_items": [...] },
  "charts": { "labels": [...], "sales": [...], "expenses": [...] },
  "recent_sales": [...],
  "top_pending_khata": [ { "id", "name", "phone", "due", "whatsapp_reminder_url" } ]
}
```

## 3. Products & Categories
- `GET /api/products/?q=<search>&category=<id>&stock=low|out|in_stock`
- `POST /api/products/` (name, brand, category, sku, barcode, purchase_price, selling_price, stock_quantity, min_stock, warranty_months, is_imei_tracked)
- `GET/PUT/DELETE /api/products/<id>/`
- `GET/POST /api/categories/`

## 4. Inventory
- `GET /api/inventory/movements/?product=<id>` — full stock ledger (purchase/sale/return/adjustment with previous→new stock)
- `POST /api/inventory/adjust/` `{product_id, action: INCREASE|DECREASE, quantity, reason, notes}`
- `GET /api/inventory/imei/?q=<imei|name>&status=IN_STOCK|SOLD`
- `POST /api/inventory/imei/` — register device (product, imei_1, imei_2, serial_number …)
- `GET /api/inventory/imei/lookup/?imei=<imei>` → `{found: true, device}` or `404 {found: false}` — full lifecycle: purchase → sale → customer, invoice no, warranty expiry

## 5. POS & Sales
### Atomic checkout
`POST /api/pos/checkout/`
```json
{
  "customer_id": 7,
  "new_customer_name": null, "new_customer_phone": null,
  "payment_method": "CASH|UPI|CARD|BANK|CREDIT",
  "discount": 0, "tax": 0, "paid_amount": 15000, "notes": "",
  "items": [ { "product_id": 3, "quantity": 1, "unit_price": 22000, "discount": 0, "device_id": 12 } ]
}
```
→ `201 { message, sale, whatsapp_share_url }`

All stock checks run **before** any write; the bill, invoice number, stock movements, IMEI status and payment are committed in one atomic database transaction. Insufficient stock / unknown product → `400` with **zero** partial writes (covered by `test_pos_insufficient_stock_rolls_back`).

- `GET /api/sales/?status=PAID|PARTIAL|UNPAID&start_date&end_date&q=<invoice|customer>`
- `GET /api/sales/<id>/` — full bill with items, IMEIs, profit

## 6. Customers & Khata
- `GET /api/customers/?q=&due=yes|cleared`
- `POST /api/customers/` · `GET/PUT/DELETE /api/customers/<id>/`
- `GET /api/customers/<id>/ledger/` → `{ customer, summary {total_sales, total_paid, outstanding_due, whatsapp_reminder_url}, sales, payments }`

## 7. Payments
- `POST /api/payments/customer/` `{customer_id, amount, payment_method, payment_date?, reference_number?, notes?}` → `201 {message, payment, remaining_due, whatsapp_receipt_url}` (khata auto-updates)
- `POST /api/payments/supplier/` `{supplier_id, amount, payment_method, …}`
- `GET /api/payments/?type=CUSTOMER_PAYMENT|SUPPLIER_PAYMENT`

## 8. Suppliers & Purchases
- `GET/POST /api/suppliers/` · `GET/PUT/DELETE /api/suppliers/<id>/`
- `GET /api/purchases/`
- `POST /api/purchases/` `{supplier_id, invoice_number?, payment_method, paid_amount, notes, items: [{product_id, quantity, unit_cost}]}` — stock increases automatically + stock movement logged + supplier payment recorded atomically.

## 9. Expenses
- `GET /api/expenses/?category=<id>&start_date&end_date`
- `POST /api/expenses/` `{title, amount, category, payment_method, expense_date, notes}`
- `GET/PUT/DELETE /api/expenses/<id>/`
- `GET/POST /api/expenses/categories/` (Rent, Electricity, Salary, Transport, Internet, Marketing, Maintenance, Other auto-seeded)

## 10. Reports (all support `?period=today|yesterday|7d|30d|this_week|this_month|last_month|custom&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`)
| Endpoint | Contents |
|---|---|
| `GET /api/reports/profit-loss/` | revenue, COGS, gross/net profit, margins, expense breakdown |
| `GET /api/reports/sales/` | count, collected, due, COGS, day-by-day trend, payment-mode split |
| `GET /api/reports/stock/` | stock cost/selling value, potential margin, low/out stock, **dead stock** (no sale 60+ days) |
| `GET /api/reports/khata/` | pending customer khata + supplier payables with WhatsApp URLs |
| `GET /api/reports/expenses/` | totals + category breakdown + trend |
| `GET /api/reports/gst/` | taxable value, GST collected, invoice register |
| `GET /api/reports/top-products/` | top products & brands by revenue/profit/units |
| `GET /api/reports/top-customers/` | top customers by spend & visits |

All financial maths is **Decimal, server-side** — the client never computes money.

## 11. Subscription — one plan only
- `GET /api/subscription/status/` → `{plan_name: "ShopZen Premium", price: 30, price_display: "₹30/month", is_active, status, start_date, end_date, days_remaining, features}`
- `POST /api/subscription/renew/` — server-side 30-day extension (payment provider webhook hook point; never trust a client `payment_success` flag)

## Security guarantees
- Every queryset is `filter(business=request.business)` — IDOR returns `404` (tested)
- No tenant id is ever read from request data
- JWT only; passwords hashed by Django; tokens in `flutter_secure_storage`
- Media/PDF URLs require an authenticated session of the owning tenant
- Expiry never deletes data — only the renew banner appears
