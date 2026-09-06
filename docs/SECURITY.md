# ShopZen Security & Multi-Tenant Isolation Documentation

## 1. Multi-tenant model

Every business object inherits `TenantModel` (`core/models.py`) which carries a non-nullable `business` foreign key. The authenticated user resolves to exactly one business via `UserProfile` (or `Business.owner` fallback) in `core/middleware.TenantMiddleware` + `api.permissions.HasActiveBusiness`. `request.business` is therefore **server-derived** — the API never reads `shop_id`, `business_id`, or `tenant_id` from request payloads or query strings. Sending such parameters has no effect on the data returned.

## 2. Enforcement pattern

Every protected endpoint:

```python
class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasActiveBusiness]
    def get_queryset(self):
        return Product.objects.filter(business=self.request.business)
```

- List views: `filter(business=…)` — other shops' rows are invisible.
- Detail/update/delete: a foreign ID simply matches no row → **404** (no existence leak, no IDOR).
- Write paths (POS checkout, purchases, payments): every `get(pk=…)` also carries `business=business`, so cross-tenant writes raise `DoesNotExist` → clean 400.

## 3. Automated proof — `api/tests.py::TenantIsolationTest`

Shop A (iPhone A, Customer A, Supplier A) vs Shop B (Samsung B, Customer B) with both owners logged in simultaneously:

| Test | Guarantee |
|---|---|
| `test_product_isolation` | A's product list contains only iPhone A |
| `test_product_idor_blocked` | `GET /api/products/<B-product-id>/` as A → 404 |
| `test_customer_isolation_and_idor` | list + detail IDOR both blocked |
| `test_supplier_isolation_and_idor` | supplier IDOR blocked |
| `test_pos_checkout_cannot_sell_other_shops_product` | A selling B's product → 400, B's stock untouched, no Sale row created |
| `test_dashboard_isolation` / `test_reports_isolation` | dashboard & all 6 report endpoints scoped to the caller |
| `test_sale_idor_blocked` | B cannot fetch A's invoice |
| `test_pos_insufficient_stock_rolls_back` | failed checkout leaves zero partial writes (atomicity) |

All 14 tests pass (`python manage.py test`).

## 4. Financial integrity

- All money is `Decimal` end-to-end (Django `DecimalField` + explicit `Decimal(str(...))` parsing). The Flutter client displays only — it never computes totals or profit.
- POS checkout: stock validation runs **before** any write; the sale, invoice number allocation, per-item stock movements, IMEI status flips and payment record commit inside one `transaction.atomic()`. A failure mid-way rolls everything back.
- Invoice numbers are unique per business (`unique_invoice_per_business` constraint) and allocated server-side.
- Payment status (`PAID/PARTIAL/UNPAID`) is derived in `Sale.save()`, never accepted from the client.
- Khata balances are computed from the ledger (`total_sales − total_payments`), not stored client-writable fields.

## 5. Authentication & secrets

- JWT (SimpleJWT): access 30 d / refresh 90 d, rotation enabled. Tokens live only in `flutter_secure_storage` (Android Keystore-backed).
- No passwords, tokens or secrets in the Flutter bundle; no credentials committed; `.env` excluded from git.
- `SIMPLE_JWT` and `SECRET_KEY` come from environment variables on Render.
- Django session auth (the website) and JWT (the app) coexist; the existing website's flows are untouched.

## 6. Payment & subscription integrity

- One plan only: **ShopZen Premium — ₹30/month** (constant in `businesses/models.py`).
- Activation/renewal is a **server-side** state change (`SubscriptionRenewAPIView`); the client can only request it — it cannot submit `payment_success` or an amount.
- Gateway webhook integration point is documented in the view; nothing in the client can forge activation.
- Expiry never deletes or hides business data — only a renewal banner is shown.

## 7. File & PDF security

Invoice PDFs (`/invoices/<id>/pdf/`) use `@business_required` + `get_object_or_404(Sale, pk=pk, business=request.business)` — guessing another shop's URL returns 404. Media uploads (product images, logos) are served per-tenant path; download endpoints re-check ownership.

## 8. Transport & headers

- HTTPS enforced by Render in production.
- CORS open by design (JWT mobile clients); CSRF still enforced for session/browser writes.
- Error responses are clean JSON messages — internal exception text is not leaked to clients (raw-`str(e)` handlers were replaced with safe messages).

## 9. Offline mode safety

Offline POS sales are queued locally and re-POSTed verbatim on reconnect (`OfflineSyncService`). A bill is only removed from the queue after the server returns **201 Created** — a sale can never appear "saved" until the backend actually has it. Duplicate prevention is server-side: if the same payload is replayed, it is validated against live stock and either committed or rejected atomically.

## 10. Remaining hardening recommendations (operator-side)

1. Set a strong random `SECRET_KEY` and `DEBUG=False` in Render env (already parameterized).
2. Add DRF throttling (`DEFAULT_THROTTLE_RATES`) at the load balancer or settings level for brute-force protection on `/api/auth/login/`.
3. Move media to S3/Render disk with signed URLs if traffic grows.
4. Run `python manage.py test` in CI on every push.
