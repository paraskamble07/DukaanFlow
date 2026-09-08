# ShopZen — Play Store Submission Package

App: **ShopZen — Mobile Shop Billing, Stock & Khata** (local-first, offline)

## 1. App identity

| Field | Value |
|---|---|
| Application ID | `com.dukaanflow.app` (keep for future updates) |
| App label | ShopZen |
| Version | 2.0.0 (code 2) |
| Target | Android 12+ (installable on older versions too) |

## 2. Short description (80 chars max)

> Mobile shop billing, stock, IMEI & khata ledger — 100% offline, no server.

## 3. Full description

ShopZen is a complete mobile-shop management app that works **entirely on your phone** — no internet, no account, no server. Your shop data stays in your hands.

BILLING / POS
• Lightning-fast counter billing — build a bill in 10 seconds
• Cash, UPI, Card, Bank and Khata (udhar) payment modes
• Partial payments and balance tracking
• Automatic invoice numbering (custom prefix)
• Share bills on WhatsApp in one tap

STOCK & INVENTORY
• Products with purchase/selling price, stock count, low-stock alerts
• Stock increases automatically on purchase entry
• Dead-stock and low-stock visibility
• Dual IMEI / serial number tracking with warranty dates
• Camera barcode/IMEI scanning

CUSTOMERS & KHATA
• Full udhar (credit) ledger per customer
• Record payments, see outstanding due at a glance
• One-tap WhatsApp payment reminders

SUPPLIERS & PURCHASES
• Supplier directory with payable balance
• Purchase entries that update stock instantly
• Supplier payment records

EXPENSES & REPORTS
• Rent, electricity, salary and custom expense categories
• Profit & Loss (true gross/net profit), Sales, Stock, Khata, GST,
  Top Products, Top Customers reports
• 7-day sales & expense trend chart on the dashboard

BACKUP & RESTORE
• Export your entire shop data as a single JSON backup file
• Restore on the same phone or a new phone
• Keep backups in Drive/WhatsApp — you own your data

PRIVACY
• No internet permission usage required for core features
• No account, no phone number, no data leaves your device
• No ads, no tracking, no analytics

Made with care for Indian mobile shop owners. Works offline forever.

## 4. Category & content rating

* Category: **Business**
* Content rating: **Everyone** (no user-generated public content)
* Contains ads: **No** · In-app purchases: **No**

## 5. Data safety form (pre-filled answers)

| Question | Answer |
|---|---|
| Does your app collect or share user data? | **No** |
| Is data encrypted in transit? | N/A (no network use) |
| Can users request data deletion? | **Yes** — Reset App Data in Settings erases everything; backups can be deleted manually |

## 6. Graphics checklist

| Asset | Requirement | Status |
|---|---|---|
| App icon | 512×512 PNG, 32-bit | use `playstore/icon-512.png` |
| Feature graphic | 1024×500 PNG | use `playstore/feature-graphic.png` |
| Phone screenshots | min 2, 16:9 or 9:16 | take on TECNO BF7 (720×1612): dashboard, POS bill, khata, reports, stock — see shot list below |
| Content rating questionnaire | fill in console | Everyone / Business |

Screenshot shot list (capture on the phone in Settings → dark or light consistently):
1. Dashboard (KPIs + trend)
2. POS screen with cart
3. Invoice success dialog with WhatsApp share
4. Customer khata detail with due
5. Stock list with low-stock badges
6. P&L report
7. Backup & Restore screen

## 7. Privacy policy

Required because the app declares no data collection: host a simple one-page
policy (GitHub Pages is free) stating that all data is stored locally on the
device, nothing is transmitted, and backups are user-managed files.

## 8. Release checklist (console)

1. Upload `release/app-release.aab`
2. Fill descriptions above, category, graphics
3. Data safety form — answers in section 5
4. Content rating — Everyone
5. Countries: India first (expand later)
6. Rollout: start with internal test track, then production
