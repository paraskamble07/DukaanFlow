# ShopZen Admin Guide (for PARAS KAMBLE)

**English** | मराठी खाली

How to create your admin account and run the ₹30 subscription business from your phone.

---

## 1. Your admin account is a normal login with a special role

The ShopZen app has **one binary**: shop owners and you use the same APK. What differs is the **server-side role** of your account:

- A normal registered user = shop owner (sees only their shop data).
- Your account = `is_superuser=True` **or** `UserProfile.role = SHOPZEN_ADMIN` → sees the extra **ShopZen Admin** section, and the server accepts your admin API calls.

There is **no admin password in the app source code** — nothing to leak. If someone steals your phone they still need your password; if someone registers their own shop they get a normal owner account and every admin API returns **403 Forbidden** for them.

## 2. Creating the admin account (one time)

**On Render (production):**

1. Render Dashboard → your service → **Shell** tab (or use the "Run Command" box).
2. Run:
   ```bash
   python manage.py createsuperuser
   ```
3. Enter your email + a strong password (this is YOUR account; never share it).
4. Promote it to ShopZen Admin (the superuser flag is enough, but the role makes intent explicit):
   ```bash
   python manage.py shell -c "from django.contrib.auth.models import User; from accounts.models import UserProfile; u=User.objects.get(email='YOUR_EMAIL'); UserProfile.objects.get_or_create(user=u, defaults={'role':'SHOPZEN_ADMIN'}); print('done')"
   ```

**Locally (for testing):** same two commands in the project venv.

## 3. Daily admin workflow

1. Open ShopZen on your phone → log in with your admin account.
2. **More → ShopZen Admin** (this tile appears ONLY for your account).
3. **Payments tab** — the work queue. For each pending shop owner:
   - Shop name, owner, email, phone, amount, **UTR**, submitted time.
   - Open GooglePay → find the ₹30 credit matching that UTR.
   - **APPROVE** → Premium activates for that shop instantly and atomically. Confirm dialog prevents slips.
   - **REJECT** (if you cannot find the money) → the owner is told "payment could not be verified" and may resubmit.
4. **Overview tab** — the business at a glance: total users, shops, active subscriptions, expired, pending/approved/rejected payments, revenue collected, recent registrations.
5. Search by UTR, shop or email using the search box. Filter PENDING / APPROVED / REJECTED with the chips.

## 4. How you know a payment request is waiting

Today the app shows the queue when you open **ShopZen Admin**. Push notifications to your device (FCM) are designed but **blocked on Firebase credentials** — see SECURITY.md / the final report's BLOCKED list for exactly what to add. Until then, open the admin screen after customers tell you "I paid" (they also see "under verification" in their app, so they know to wait).

## 5. Safety guarantees you can rely on

- **Double approval impossible:** once approved, the request leaves PENDING; a second APPROVE call (even replayed with the same request id) returns 404 and changes nothing.
- **Audit trail:** every approve/reject/blocked attempt stored with your admin identity and timestamp (`AdminAuditLog`), viewable in Django admin.
- **No client-side activation:** the app can never set Premium by itself; it only displays what `/api/subscription/status/` says.
- **Expiry is enforced by dates on the server**, not by any local flag on the customer's phone.

## 6. Audit log — where to look

Django admin (`/admin/`) → **Admin audit logs**: admin user, action (`subscription_approve` / `subscription_reject` / `blocked_*`), target, detail, result, timestamp. Payment requests themselves (with full history) live under **Subscription payment requests**.

## 7. If something looks wrong

| Symptom | Likely cause | Action |
|---|---|---|
| "Could not load admin stats" | You're logged in with a non-admin account, or server restarted | Check login; retry; check /api/health/ |
| Approve button says 404 | Request already reviewed (by you earlier) | Refresh the list |
| Owner says they paid but no request | They didn't tap SUBMIT in the app | Ask them to enter UTR and submit |

---

## मराथी — Admin मार्गदर्शक

1. **Admin खाते:** Render Dashboard → Shell → `python manage.py createsuperuser` → तुमचा email आणि मजबूत पासवर्ड द्या. हे खाते फक्त तुमचे.
2. **रोजचे काम:** ॲप मध्ये admin खात्याने login → More → ShopZen Admin → Payments टॅब → UTR तपासा → APPROVE (Premium सुरू) किंवा REJECT.
3. **Overview टॅब:** एकूण वापरकर्ते, दुकाने, सक्रिय/संपलेली सदस्यत्वे, उत्पन्न.
4. **सुरक्षा:** दुहेरी approve अशक्य; प्रत्येक कृती audit log मध्ये; ॲप स्वतः Premium कधीही सुरू करू शकत नाही.
5. **Notification:** फोनवर push सूचना सध्या उपलब्ध नाहीत (Firebase keys नाहीत) — ग्राहक "मी भरलं" म्हटल्यावर admin स्क्रीन उघडून बघा.
