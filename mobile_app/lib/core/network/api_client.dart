import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import 'local_dio.dart';

/// ShopZen v2 — LOCAL-FIRST.
///
/// The app now runs entirely on the device's SQLite database. `ApiClient.dio`
/// is a [LocalDio] instance: every existing screen and provider keeps
/// calling it exactly as before, but requests are answered from the local
/// database instead of a server. No internet, no Render, no laptop — ever.
///
/// The field is still named `dio` and typed `Dio` so no call site changes;
/// LocalDio implements the request methods the app uses.
class ApiClient {
  late final LocalDio dio;

  ApiClient() {
    dio = LocalDio();
  }
}
