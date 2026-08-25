from datetime import date

def business_context(request):
    business = getattr(request, 'business', None)
    return {
        'current_business': business,
        'today': date.today(),
        'app_name': 'DukaanFlow',
        'app_tagline': 'Run your mobile shop smarter.',
    }
