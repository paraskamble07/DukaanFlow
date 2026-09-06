import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class AppLocalizations {
  final Locale locale;
  AppLocalizations(this.locale);

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations) ??
        AppLocalizations(const Locale('en'));
  }

  static const _localizedValues = <String, Map<String, String>>{
    'en': {
      'app_name': 'DukaanFlow',
      'tagline': 'Run your mobile shop smarter',
      'dashboard': 'Dashboard',
      'pos_billing': 'POS Billing',
      'inventory': 'Inventory',
      'customers': 'Customers',
      'khata': 'Khata (Udhar)',
      'more': 'More',
      'today_sales': "Today's Sales",
      'today_profit': "Today's Profit",
      'today_expenses': "Today's Expenses",
      'outstanding_khata': 'Outstanding Udhar',
      'new_sale': 'New Sale',
      'add_product': 'Add Product',
      'add_customer': 'Add Customer',
      'scan_imei': 'Scan IMEI',
      'low_stock_alert': 'Low Stock Alert',
      'complete_sale': 'Complete Sale',
      'send_whatsapp': 'Send WhatsApp Reminder',
      'grand_total': 'Grand Total',
      'paid_amount': 'Paid Amount',
      'due_amount': 'Balance Due',
      'language': 'Language',
      'theme': 'Theme',
      'logout': 'Logout',
    },
    'hi': {
      'app_name': 'दुकानफ्लो',
      'tagline': 'अपनी मोबाइल दुकान को स्मार्ट तरीके से चलाएं',
      'dashboard': 'डैशबोर्ड',
      'pos_billing': 'पीओएस बिलिंग',
      'inventory': 'स्टॉक व उत्पाद',
      'customers': 'ग्राहक',
      'khata': 'खाता (उधार)',
      'more': 'अधिक',
      'today_sales': 'आज की कुल बिक्री',
      'today_profit': 'आज का शुद्ध लाभ',
      'today_expenses': 'आज के खर्चे',
      'outstanding_khata': 'मार्केट उधार (बाकी)',
      'new_sale': 'नया बिल बनाएं',
      'add_product': 'नया सामान जोड़ें',
      'add_customer': 'नया ग्राहक जोड़ें',
      'scan_imei': 'IMEI स्कैन करें',
      'low_stock_alert': 'स्टॉक खत्म होने की चेतावनी',
      'complete_sale': 'बिल पूरा करें',
      'send_whatsapp': 'व्हाट्सएप पर तगादा भेजें',
      'grand_total': 'कुल देय राशि',
      'paid_amount': 'जमा राशि',
      'due_amount': 'बाकी उधार',
      'language': 'भाषा बदलें',
      'theme': 'थीम (डार्क / लाइट)',
      'logout': 'लॉग आउट',
    },
    'mr': {
      'app_name': 'दुकानफ्लो',
      'tagline': 'आपले मोबाईल दुकान स्मार्टपणे चालवा',
      'dashboard': 'डॅशबोर्ड',
      'pos_billing': 'पीओएस बिलिंग',
      'inventory': 'साठा व वस्तू',
      'customers': 'ग्राहक',
      'khata': 'खाते (उधार)',
      'more': 'इतर',
      'today_sales': 'आजची एकूण विक्री',
      'today_profit': 'आजचा निव्वळ नफा',
      'today_expenses': 'आजचे खर्च',
      'outstanding_khata': 'बाजार बाकी (उधार)',
      'new_sale': 'नवीन बिल बनवा',
      'add_product': 'नवीन वस्तू जोडा',
      'add_customer': 'नवीन ग्राहक जोडा',
      'scan_imei': 'IMEI स्कॅन करा',
      'low_stock_alert': 'साठा संपत आल्याची सूचना',
      'complete_sale': 'बिल पूर्ण करा',
      'send_whatsapp': 'व्हॉट्सअ‍ॅपवर आठवण पाठवा',
      'grand_total': 'एकूण रक्कम',
      'paid_amount': 'जमा रक्कम',
      'due_amount': 'बाकी रक्कम',
      'language': 'भाषा बदला',
      'theme': 'थीम निवडा',
      'logout': 'लॉग आऊट',
    }
  };

  String translate(String key) {
    return _localizedValues[locale.languageCode]?[key] ??
        _localizedValues['en']?[key] ??
        key;
  }
}

class AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const AppLocalizationsDelegate();

  @override
  bool isSupported(Locale locale) => ['en', 'hi', 'mr'].contains(locale.languageCode);

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(AppLocalizations(locale));
  }

  @override
  bool shouldReload(AppLocalizationsDelegate old) => false;
}
