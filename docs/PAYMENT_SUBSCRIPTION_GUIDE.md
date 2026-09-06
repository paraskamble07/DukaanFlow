# ShopZen ₹30 Subscription & Payment Guide

**English** | मराठी खाली

How the ₹30/month ShopZen Premium subscription works, how a shop owner pays, and how YOU (the only ShopZen Admin) verify payments and activate Premium.

---

## 1. The payment model — manual verification, no auto-activation

```
Shop Owner                    Server (Django)                     You (Admin)
    │                              │                                  │
    │ Sees QR + ₹30 + UPI ID       │                                  │
    │ Pays via ANY UPI app         │                                  │
    │ Enters UTR in ShopZen        │                                  │
    │ Submits                      │ Creates request PENDING          │
    │                              │ (Premium NOT activated)          │
    │                              │                                  │
    │                              │◀──── you check your UPI app ─────│
    │                              │      does the UTR + ₹30 exist?   │
    │                              │                                  │
    │                              │ APPROVE (atomic) or REJECT        │
    │  Premium ACTIVE + expiry ◀───│ Only approval activates Premium  │
    │                              │ Double-approve = blocked (404)   │
```

**Golden rules (enforced in code, not by trust):**

1. Submitting a UTR **never** activates Premium. It only creates a `PENDING` request.
2. Only an authenticated **ShopZen Admin** can approve or reject — checked server-side on every request (`IsShopZenAdmin`).
3. Approve is **atomic**: `transaction.atomic()` + `select_for_update()` + `status=PENDING` filter. A double-tap, replay, or two admins at once cannot double-activate or double-extend.
4. ₹60 pays 2 months, ₹90 pays 3 (any multiple of ₹30). Extra money beyond a multiple (e.g. ₹45) is **rejected** as an invalid amount at submit time.
5. Approvals **stack** on the current expiry: if 5 days remain and ₹30 is approved, the new expiry = today + 30 days **after** the remaining 5 (total 35 days of value kept). *(Back-to-back approvals use `max(current_expiry, today)` as the base.)*
6. Every action is written to the **AdminAuditLog** (who/what/when/result), including blocked attempts.

## 2. Where the money configuration lives

No secrets are stored in the Flutter app. The app **asks the server** for the current payment details:

| Setting | Env var | Current value |
|---|---|---|
| Price | computed from `SHOPZEN_PREMIUM_PRICE` (settings) | ₹30 / 30 days |
| UPI ID | `SHOPZEN_UPI_ID` | `kambleparas220-1@okaxis` |
| Payee name | `SHOPZEN_PAYEE_NAME` | `Paras Kamble` |
| QR image | `SHOPZEN_QR_IMAGE_URL` | `https://dukaanflow.onrender.com/static/images/shopzen_payment_qr.png` |

Change any of these later by setting the env var on Render (Dashboard → Environment) and redeploying — **no app update needed**.

## 3. Shop owner flow (what your customers see)

1. **More → ShopZen Premium** (₹30/month — subscription status).
2. If expired and no pending request: the app shows **your QR code**, the UPI ID and a UTR field.
3. They pay ₹30 in GooglePay/PhonePe/Paytm/BHIM (any UPI app), copy the UTR/reference number from their payment receipt.
4. They type the UTR and tap **I HAVE PAID — SUBMIT**.
5. The card changes to **"Payment Under Verification"** — they can tap *Check Status* anytime.
6. After you approve: next visit shows **ACTIVE • X days left**. No app restart needed.
7. If you reject: they see the rejection reason and can pay + submit again.

## 4. Admin flow (you) — two ways to verify

**Option A — in the app (recommended):**
1. Log in to ShopZen with your admin account (see ADMIN_GUIDE.md for how the account is created).
2. **More → ShopZen Admin** (visible only to your admin account).
3. **Payments tab** is the work queue: shop, owner, email, phone, amount, UTR, submitted time.
4. Open your UPI app, find the ₹30 credit with that UTR (or from that shop's phone number).
5. **APPROVE** (green) — activates Premium atomically. **REJECT** (red) — asks for nothing more; owner can resubmit. Every action asks for confirmation first.
6. **Overview tab**: total users/shops, active & expired subscriptions, pending/approved/rejected counts, revenue, recent registrations.

**Option B — Django admin (backup):** `https://dukaanflow.onrender.com/admin/` → Subscription payment requests. Read-only inspection; do the approve/reject from Option A so the audit log and business rules are applied.

## 5. Payment history & audit (permanent)

Every request stores: shop, owner, amount, UTR, submitted time, status, reviewed by, reviewed time, rejection reason, subscription start, subscription expiry. Nothing is deleted. The AdminAuditLog additionally records every approve/reject/blocked attempt with admin identity and timestamp.

## 6. What is NOT automated (on purpose)

- No payment gateway — money goes **directly to your UPI** (no commission, no third party).
- No automatic bank verification — a screenshot or UTR alone proves nothing; only your approval matters.
- No auto-reminder emails — the owner's app shows "EXPIRED" and the renewal card automatically.

---

## मराठी — ₹30 सदस्यत्व आणि पेमेंट मार्गदर्शक

**नियम (कोडमध्येच लागू आहेत):**

1. UTR भरला म्हणजे Premium सुरू होत **नाही** — फक्त "प्रलंबित" (PENDING) विनंती तयार होते.
2. फक्त तुमचे (admin) खाते approve करू शकते — हे प्रत्येक वेळी सर्व्हर तपासतो.
3. Approve एकाच वेळेस अनेकजण दाबले तरी दुहेरी होत नाही (atomic + lock).
4. ₹60 = 2 महिने, ₹90 = 3 महिने. ₹30 च्या पूर्ण पट्टीत नसलेला रक्कम नाकारला जातो.
5. प्रत्येक कृतीची नोंद (कोण, केव्हा, काय) audit log मध्ये कायम राहते.

**दुकानदारासाठी:** More → ShopZen Premium → QR स्कॅन करून ₹30 भरा → UTR नंबर ॲप मध्ये टाका → "I HAVE PAID" दाबा → तुमच्या approve होईपर्यंत "Verification साठी प्रतीक्षा" दिसेल.

**तुमच्यासाठी (admin):** More → ShopZen Admin → Payments टॅब → UTR तुमच्या UPI ॲप मध्ये तपासा → APPROVE किंवा REJECT.
