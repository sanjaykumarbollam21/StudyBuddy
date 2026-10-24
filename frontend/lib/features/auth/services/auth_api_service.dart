import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/user_model.dart';

class AuthApiService {
  final ApiClient _client = ApiClient();

  Future<Map<String, dynamic>> signup({
    required String email,
    required String password,
    String? fullName,
  }) async {
    final response = await _client.post(
      AppConfig.signupEndpoint,
      body: {
        'email': email,
        'password': password,
        'full_name': fullName,
      },
    );
    return response as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await _client.post(
      AppConfig.loginEndpoint,
      body: {
        'email': email,
        'password': password,
      },
    );
    return response as Map<String, dynamic>;
  }

  Future<UserModel> getMe() async {
    final response = await _client.get(AppConfig.meEndpoint);
    return UserModel.fromJson(response as Map<String, dynamic>);
  }

  Future<UserModel> updateProfile(UserProfile profile) async {
    final response = await _client.put(
      AppConfig.profileEndpoint,
      body: profile.toJson(),
    );
    return UserModel.fromJson(response as Map<String, dynamic>);
  }

  Future<UserModel> updateSettings(UserSettings settings) async {
    final response = await _client.put(
      AppConfig.settingsEndpoint,
      body: settings.toJson(),
    );
    return UserModel.fromJson(response as Map<String, dynamic>);
  }

  Future<void> forgotPassword(String email) async {
    await _client.post(
      AppConfig.forgotPasswordEndpoint,
      body: {'email': email},
    );
  }
}
