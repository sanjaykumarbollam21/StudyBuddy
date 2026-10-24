class AppException implements Exception {
  final String message;
  final int? statusCode;

  AppException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  NetworkException([super.message = 'Unable to connect to Study Buddy server. Please verify your connection.']);
}

class AuthException extends AppException {
  AuthException(super.message) : super(statusCode: 401);
}

class ValidationException extends AppException {
  ValidationException(super.message) : super(statusCode: 422);
}
