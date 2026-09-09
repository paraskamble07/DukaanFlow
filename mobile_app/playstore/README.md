# ShopZen — Play Store Submission Package

App: **ShopZen — Mobile Shop Billing, Stock & Khata** (cloud SaaS, ₹30/month Premium)

## 1. App identity

| Field | Value |
|---|---|
| Application ID | `com.dukaanflow.app` (keep for future updates) |
| App label | ShopZen |
| Version | 1.0.0 (code 1) |
| Target | Android 12+ (installable on older versions too) |
| Backend | `https://dukaanflow.onrender.com` (HTTPS/JWT) |

## 2. Short description (80 chars max)

> Mobile shop billing, stock, IMEI & khata — sell faster, track profit.

## 3. Full description

ShopZen is a complete mobile-shop management app built for Indian mobile & electronics shop owners.

**Sell in 10 seconds** — Lightning-fast POS billing. Cart, discounts, GST, split/partial payment and Khata (udhar) sales. Invoice numbers are automatic and stock is deducted atomically on the server — no overselling, even on a bad connection (queued offline sales sync safely with duplicate protection).

**Know your stock** — Products, dual-IMEI & serial tracking, low-stock alerts, live store valuation, stock movement ledger for every change.

**Khata (udhar) ledger** — Customer outstanding balances, receive payments with one tap, WhatsApp payment reminders, full transaction history.

**True profit analytics** — P&L, daily sales, stock valuation, dead stock, khata, expenses, GST register, top products & top customers. Every report uses server-side exact decimal money math.

**Suppliers & purchases** — Purchase entries raise stock automatically, supplier payables, purchase history.

**Your data, safe in the cloud** — Register with email & password. Your shop data lives on a secure server, so it follows you to any phone — lose your phone, lose nothing.

**ShopZen Premium** — ₹30/month after your trial. Pay via UPI, enter the reference number, and it's activated after verification in your admin dashboard. No card details are ever collected in the app.

Works anywhere in India — all you need is your phone and internet.

Developed by PARAS KAMBLE.

## 4. Category & content rating

- App category: **Business**
- Content rating: **Everyone** (no user-generated content displayed publicly)
- Target audience: 18+ (business tool), declared as such in Data Safety

## 5. Data safety form (exact answers)

| Question | Answer |
|---|---|
| Does your app collect or share user data? | **Yes** |
| What data is collected? | Name, email, phone number, address (account & shop management); purchase/transaction records (app functionality) |
| Is data encrypted in transit? | **Yes** (HTTPS/TLS to the API) |
| Can users request data deletion? | **Yes** — contacting support (support contact in Play listing); shop data is deleted from the server on verified request |
| Is data shared with third parties? | **No** |
| Does the app use encryption at rest? | Handled server-side by the hosting provider's managed database |

## 6. Screenshots (7 required, min 320px, max 8MB, 16:9 or 9:16)

Take from the actual app (phone or emulator, 1080×2400 recommended):
1. Splash/branding screen — "ShopZen — Smart Shop Management — Developed by PARAS KAMBLE"
2. Dashboard — today's sales/profit cards + 7-day chart
3. POS checkout — cart with totals & Generate button
4. Sale success dialog — invoice number + WhatsApp share button
5. Products/stock list — with low-stock badge
6. Customer khata — outstanding due + WhatsApp reminder button
7. Reports screen (P&L or top products)

## 7. Graphics

| Asset | File | Spec |
|---|---|---|
| App icon (512×512 PNG) | `icon-512.png` | 32-bit PNG, no transparency for adaptive icon fallback |
| Feature graphic (1024×500) | `feature-graphic.png` | shown atop the listing |

## 8. Privacy policy

Required because the app collects account data. Host a page (GitHub Pages is free) covering:
- What is collected: name, email, phone, shop details, business records (sales, stock, khata)
- Why: to provide the service; data is stored on the app's server only
- Sharing: none with third parties
- Deletion: email support to request full account & data deletion
- Contact: your support email

## 9. Release checklist (exact order)

1. Build AAB: `cd mobile_app && flutter build appbundle --release` (default URL = production)
2. Create release keystore + `key.properties` (see `docs/ANDROID_BUILD.md` §7) — **never commit or lose it**
3. Bump `pubspec.yaml` version (e.g. `1.0.1+2`)
4. Create Play Console app → set category Business, content rating, data safety (§5), privacy policy URL
5. Upload `app-release.aab` to the **internal testing** track first
6. Install from the testing link on a real phone; run the 21-point checklist from `docs/TESTING.md`
7. Promote to production only after the Render backend is verified live (`/api/health/` returns ok)

## 10. Do NOT claim

- Not published yet — the listing is only *prepared* by this package.
- Premium payments are verified manually by the admin; do not advertise "instant activation".
