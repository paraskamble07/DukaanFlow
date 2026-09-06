import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import '../storage/local_storage.dart';

class ApiClient {
  late final Dio dio;

  ApiClient() {
    dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await LocalStorageService.getAccessToken();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer ' + token;
        }
        return handler.next(options);
      },
      onError: (DioException error, handler) async {
        // Handle 401 token refresh
        if (error.response?.statusCode == 401) {
          final refreshToken = await LocalStorageService.getRefreshToken();
          if (refreshToken != null) {
            try {
              final refreshDio = Dio(BaseOptions(baseUrl: ApiConstants.baseUrl));
              final res = await refreshDio.post(
                ApiConstants.refreshToken,
                data: {'refresh': refreshToken},
              );
              if (res.statusCode == 200) {
                final newAccess = res.data['access'];
                await LocalStorageService.saveTokens(newAccess, refreshToken);
                
                // Retry original request
                final opts = error.requestOptions;
                opts.headers['Authorization'] = 'Bearer ' + newAccess;
                final cloneReq = await dio.request(
                  opts.path,
                  options: Options(method: opts.method, headers: opts.headers),
                  data: opts.data,
                  queryParameters: opts.queryParameters,
                );
                return handler.resolve(cloneReq);
              }
            } catch (e) {
              await LocalStorageService.clearAuth();
            }
          }
        }
        return handler.next(error);
      },
    ));
  }
}
