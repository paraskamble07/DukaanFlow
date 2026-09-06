from rest_framework import generics
from expenses.models import Expense, ExpenseCategory, DEFAULT_EXPENSE_CATEGORIES
from api.serializers import ExpenseSerializer, ExpenseCategorySerializer
from api.permissions import HasActiveBusiness

def ensure_expense_categories(business):
    for name in DEFAULT_EXPENSE_CATEGORIES:
        ExpenseCategory.objects.get_or_create(business=business, name=name)

class ExpenseCategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExpenseCategorySerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        ensure_expense_categories(self.request.business)
        return ExpenseCategory.objects.filter(business=self.request.business)

    def perform_create(self, serializer):
        serializer.save(business=self.request.business)

class ExpenseListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        ensure_expense_categories(self.request.business)
        qs = Expense.objects.filter(business=self.request.business).select_related('category')
        cat_id = self.request.query_params.get('category')
        if cat_id:
            qs = qs.filter(category_id=cat_id)
        start_date = self.request.query_params.get('start_date')
        if start_date:
            qs = qs.filter(expense_date__gte=start_date)
        end_date = self.request.query_params.get('end_date')
        if end_date:
            qs = qs.filter(expense_date__lte=end_date)
        return qs

    def perform_create(self, serializer):
        serializer.save(business=self.request.business)

class ExpenseDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [HasActiveBusiness]

    def get_queryset(self):
        return Expense.objects.filter(business=self.request.business)
