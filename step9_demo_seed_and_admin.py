import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

seed_command_code = """from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from businesses.models import Business
from accounts.models import UserProfile
from customers.models import Customer
from products.models import Product, Category
from inventory.models import StockMovement, MobileDevice
from suppliers.models import Supplier
from purchases.models import Purchase, PurchaseItem
from sales.models import Sale, SaleItem
from payments.models import Payment
from expenses.models import Expense, ExpenseCategory

class Command(BaseCommand):
    help = 'Seeds realistic Indian demo data for DukaanFlow SaaS (Paras Mobile Hub)'

    def handle(self, *args, **options):
        self.stdout.write("Seeding DukaanFlow Demo Data...")

        # 1. Create Demo Owner & Business
        user, created = User.objects.get_or_create(
            username='demo@dukaanflow.com',
            defaults={
                'email': 'demo@dukaanflow.com',
                'first_name': 'Paras',
                'last_name': 'Jain',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        user.set_password('demo12345')
        user.save()

        business, _ = Business.objects.get_or_create(
            owner=user,
            defaults={
                'name': 'Paras Mobile Hub',
                'owner_name': 'Paras Jain',
                'phone': '9820011223',
                'email': 'paras@parasmobile.in',
                'address': 'Shop #4, Galaxy Plaza, Station Road, Dadar West',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400028',
                'gstin': '27AABCP1234F1Z5',
                'invoice_prefix': 'PMH-',
                'plan_tier': 'PRO',
                'invoice_footer': 'Thank you for choosing Paras Mobile Hub! All smartphones include official brand warranty. Physical/liquid damage not covered.'
            }
        )

        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'business': business, 'phone': '9820011223', 'role': 'OWNER'}
        )
        profile.business = business
        profile.save()

        # 2. Categories
        cat_smartphones, _ = Category.objects.get_or_create(business=business, name='Smartphones')
        cat_chargers, _ = Category.objects.get_or_create(business=business, name='Chargers')
        cat_cables, _ = Category.objects.get_or_create(business=business, name='Cables')
        cat_covers, _ = Category.objects.get_or_create(business=business, name='Covers & Cases')
        cat_glass, _ = Category.objects.get_or_create(business=business, name='Tempered Glass')
        cat_power, _ = Category.objects.get_or_create(business=business, name='Power Banks')

        # 3. Suppliers
        sup_dist, _ = Supplier.objects.get_or_create(
            business=business,
            company_name='National Mobile Distributors',
            defaults={
                'name': 'Sanjay Mehta',
                'phone': '9819988776',
                'email': 'sanjay@nationaldist.com',
                'address': 'Lamington Road, Grant Road East, Mumbai',
                'gstin': '27AABCN9988H1Z2'
            }
        )
        sup_acc, _ = Supplier.objects.get_or_create(
            business=business,
            company_name='Mumbai Accessories Hub',
            defaults={
                'name': 'Vikas Patel',
                'phone': '9833445566',
                'email': 'vikas@mumbaiacc.in',
                'address': 'Fort Market, Mumbai',
                'gstin': '27ABCDE1122K1Z9'
            }
        )

        # 4. Products
        p_galaxy, _ = Product.objects.get_or_create(
            business=business,
            name='Samsung Galaxy A56 5G (8GB/128GB)',
            defaults={
                'brand': 'Samsung',
                'category': cat_smartphones,
                'sku': 'SAM-A56-128',
                'barcode': '8901234567890',
                'purchase_price': Decimal('24500.00'),
                'selling_price': Decimal('28999.00'),
                'stock_quantity': 10,
                'min_stock': 3,
                'warranty_months': 12,
                'is_imei_tracked': True,
                'supplier': sup_dist
            }
        )

        p_iphone, _ = Product.objects.get_or_create(
            business=business,
            name='Apple iPhone 15 (128GB Blue)',
            defaults={
                'brand': 'Apple',
                'category': cat_smartphones,
                'sku': 'APL-IP15-128BL',
                'barcode': '194253712345',
                'purchase_price': Decimal('61000.00'),
                'selling_price': Decimal('69900.00'),
                'stock_quantity': 6,
                'min_stock': 2,
                'warranty_months': 12,
                'is_imei_tracked': True,
                'supplier': sup_dist
            }
        )

        p_redmi, _ = Product.objects.get_or_create(
            business=business,
            name='Redmi Note 13 Pro 5G (8GB/256GB)',
            defaults={
                'brand': 'Xiaomi',
                'category': cat_smartphones,
                'sku': 'MI-RN13P-256',
                'barcode': '890765432109',
                'purchase_price': Decimal('19200.00'),
                'selling_price': Decimal('23999.00'),
                'stock_quantity': 8,
                'min_stock': 3,
                'warranty_months': 12,
                'is_imei_tracked': True,
                'supplier': sup_dist
            }
        )

        p_charger, _ = Product.objects.get_or_create(
            business=business,
            name='25W Type-C Super Fast Adapter',
            defaults={
                'brand': 'Samsung',
                'category': cat_chargers,
                'sku': 'SAM-25W-ADPT',
                'purchase_price': Decimal('650.00'),
                'selling_price': Decimal('1299.00'),
                'stock_quantity': 25,
                'min_stock': 5,
                'warranty_months': 6,
                'is_imei_tracked': False,
                'supplier': sup_acc
            }
        )

        p_cable, _ = Product.objects.get_or_create(
            business=business,
            name='65W Braided Type-C to Type-C Fast Cable',
            defaults={
                'brand': 'BoAt',
                'category': cat_cables,
                'sku': 'BOAT-65W-CAB',
                'purchase_price': Decimal('180.00'),
                'selling_price': Decimal('499.00'),
                'stock_quantity': 40,
                'min_stock': 10,
                'warranty_months': 6,
                'is_imei_tracked': False,
                'supplier': sup_acc
            }
        )

        p_glass, _ = Product.objects.get_or_create(
            business=business,
            name='11D Edge-to-Edge Tempered Glass (Universal)',
            defaults={
                'brand': 'GorillaShield',
                'category': cat_glass,
                'sku': 'TEMP-11D-UNI',
                'purchase_price': Decimal('45.00'),
                'selling_price': Decimal('199.00'),
                'stock_quantity': 65,
                'min_stock': 15,
                'warranty_months': 0,
                'is_imei_tracked': False,
                'supplier': sup_acc
            }
        )

        # 5. Tracked Mobile Devices / IMEIs
        devices_data = [
            (p_galaxy, '864521098765431', '864521098765432', 'Awesome Blue', 'Samsung'),
            (p_galaxy, '864521098765433', '864521098765434', 'Awesome Graphite', 'Samsung'),
            (p_iphone, '357890123456781', '', '128GB Blue', 'Apple'),
            (p_iphone, '357890123456782', '', '128GB Black', 'Apple'),
            (p_redmi, '869012345678901', '869012345678902', 'Midnight Black', 'Xiaomi'),
        ]
        for prod, imei1, imei2, model, brand in devices_data:
            MobileDevice.objects.get_or_create(
                business=business,
                imei_1=imei1,
                defaults={
                    'product': prod,
                    'imei_2': imei2,
                    'model_name': model,
                    'brand': brand,
                    'purchase_price': prod.purchase_price,
                    'selling_price': prod.selling_price,
                    'status': 'IN_STOCK'
                }
            )

        # 6. Customers
        c_rahul, _ = Customer.objects.get_or_create(
            business=business,
            phone='9820123456',
            defaults={
                'name': 'Rahul Patil',
                'email': 'rahul.patil@gmail.com',
                'address': 'A-102, Shiv Shrushti CHS, Dadar West',
                'credit_limit': Decimal('10000.00'),
                'notes': 'Regular customer, works at HDFC Bank'
            }
        )

        c_amit, _ = Customer.objects.get_or_create(
            business=business,
            phone='9833987654',
            defaults={
                'name': 'Amit Jadhav',
                'email': 'amit.jadhav@yahoo.co.in',
                'address': 'Flat 4B, Sai Sadan, Prabhadevi',
                'credit_limit': Decimal('5000.00'),
                'notes': 'Preferred payment method: UPI'
            }
        )

        c_sneha, _ = Customer.objects.get_or_create(
            business=business,
            phone='9811223344',
            defaults={
                'name': 'Sneha Desai',
                'address': 'Matunga East, Mumbai',
                'credit_limit': Decimal('8000.00')
            }
        )

        # 7. Sample POS Sales & Partial Payments (Khata)
        today = timezone.now()
        
        # Sale 1: Rahul Patil - Galaxy A56 + 25W Charger (Partial Paid -> Due ₹3,999)
        inv1 = "PMH-1001"
        if not Sale.objects.filter(business=business, invoice_number=inv1).exists():
            s1 = Sale.objects.create(
                business=business,
                customer=c_rahul,
                invoice_number=inv1,
                subtotal=Decimal('30298.00'),
                discount=Decimal('299.00'),
                tax_amount=Decimal('0.00'),
                total_amount=Decimal('29999.00'),
                paid_amount=Decimal('26000.00'),
                due_amount=Decimal('3999.00'),
                payment_status='PARTIAL',
                payment_method='UPI',
                sale_date=today - timedelta(days=2),
                notes='Customer promised to clear remaining ₹3,999 next week.'
            )
            si1 = SaleItem.objects.create(
                sale=s1,
                product=p_galaxy,
                quantity=1,
                unit_price=Decimal('28999.00'),
                discount=Decimal('299.00'),
                total_price=Decimal('28700.00'),
                imei_numbers='IMEI: 864521098765431'
            )
            si2 = SaleItem.objects.create(
                sale=s1,
                product=p_charger,
                quantity=1,
                unit_price=Decimal('1299.00'),
                discount=Decimal('0.00'),
                total_price=Decimal('1299.00')
            )
            # Mark device as sold
            dev = MobileDevice.objects.filter(business=business, imei_1='864521098765431').first()
            if dev:
                dev.status = 'SOLD'
                dev.customer = c_rahul
                dev.sale_item = si1
                dev.sale_date = s1.sale_date
                dev.warranty_expiry_date = (today + timedelta(days=365)).date()
                dev.save()

            Payment.objects.create(
                business=business,
                payment_type='CUSTOMER_PAYMENT',
                customer=c_rahul,
                sale=s1,
                amount=Decimal('26000.00'),
                payment_method='UPI',
                payment_date=s1.sale_date.date(),
                reference_number='UPI/423188992100',
                notes='Initial deposit for Galaxy A56'
            )

        # Sale 2: Amit Jadhav - iPhone 15 + Tempered Glass (Fully Paid Cash)
        inv2 = "PMH-1002"
        if not Sale.objects.filter(business=business, invoice_number=inv2).exists():
            s2 = Sale.objects.create(
                business=business,
                customer=c_amit,
                invoice_number=inv2,
                subtotal=Decimal('70099.00'),
                discount=Decimal('99.00'),
                total_amount=Decimal('70000.00'),
                paid_amount=Decimal('70000.00'),
                due_amount=Decimal('0.00'),
                payment_status='PAID',
                payment_method='CARD',
                sale_date=today - timedelta(days=1),
                notes='HDFC Credit Card EMI swipe'
            )
            si_ip = SaleItem.objects.create(
                sale=s2,
                product=p_iphone,
                quantity=1,
                unit_price=Decimal('69900.00'),
                discount=Decimal('0.00'),
                total_price=Decimal('69900.00'),
                imei_numbers='IMEI: 357890123456781'
            )
            SaleItem.objects.create(
                sale=s2,
                product=p_glass,
                quantity=1,
                unit_price=Decimal('199.00'),
                discount=Decimal('99.00'),
                total_price=Decimal('100.00')
            )
            dev_ip = MobileDevice.objects.filter(business=business, imei_1='357890123456781').first()
            if dev_ip:
                dev_ip.status = 'SOLD'
                dev_ip.customer = c_amit
                dev_ip.sale_item = si_ip
                dev_ip.sale_date = s2.sale_date
                dev_ip.warranty_expiry_date = (today + timedelta(days=365)).date()
                dev_ip.save()

            Payment.objects.create(
                business=business,
                payment_type='CUSTOMER_PAYMENT',
                customer=c_amit,
                sale=s2,
                amount=Decimal('70000.00'),
                payment_method='CARD',
                payment_date=s2.sale_date.date(),
                reference_number='POS-CARD-9921',
                notes='Full payment for iPhone 15'
            )

        # 8. Daily Expenses
        exp_rent, _ = ExpenseCategory.objects.get_or_create(business=business, name='Shop Rent')
        exp_elec, _ = ExpenseCategory.objects.get_or_create(business=business, name='Electricity Bill')
        exp_tea, _ = ExpenseCategory.objects.get_or_create(business=business, name='Tea & Refreshments')

        Expense.objects.get_or_create(
            business=business,
            title='Monthly Shop Rent - Galaxy Plaza',
            defaults={
                'category': exp_rent,
                'amount': Decimal('22000.00'),
                'payment_method': 'BANK',
                'expense_date': today.date() - timedelta(days=5),
                'notes': 'NEFT to landlord Shri R. K. Sharma'
            }
        )

        Expense.objects.get_or_create(
            business=business,
            title='Adani Electricity Bill (Shop AC)',
            defaults={
                'category': exp_elec,
                'amount': Decimal('3450.00'),
                'payment_method': 'UPI',
                'expense_date': today.date() - timedelta(days=3)
            }
        )

        Expense.objects.get_or_create(
            business=business,
            title='Counter Tea & Snacks for Customers',
            defaults={
                'category': exp_tea,
                'amount': Decimal('320.00'),
                'payment_method': 'CASH',
                'expense_date': today.date()
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo shop 'Paras Mobile Hub' seeded successfully!"))
        self.stdout.write("Login credentials:")
        self.stdout.write("Email / Username: demo@dukaanflow.com")
        self.stdout.write("Password: demo12345")
"""
with open(os.path.join(BASE_DIR, "core", "management", "commands", "seed_demo_data.py"), "w", encoding="utf-8") as f:
    f.write(seed_command_code)

print("Management command seed_demo_data created successfully!")
