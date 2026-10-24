import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/tutor_model.dart';

class TutorApiService {
  final ApiClient _client = ApiClient();

  Future<TutorResponseModel> askTutor(
    String query, {
    List<String>? documentIds,
    String? subject,
    String? collection,
    String groundingMode = 'materials_plus_general',
    String? sessionId,
  }) async {
    final body = <String, dynamic>{
      'query': query,
      'grounding_mode': groundingMode,
    };
    if (documentIds != null && documentIds.isNotEmpty) {
      body['document_ids'] = documentIds;
    }
    if (subject != null && subject.isNotEmpty) {
      body['subject'] = subject;
    }
    if (collection != null && collection.isNotEmpty) {
      body['collection'] = collection;
    }
    if (sessionId != null && sessionId.isNotEmpty) {
      body['session_id'] = sessionId;
    }

    final response = await _client.post(
      '${AppConfig.baseUrl}/tutor/ask',
      body: body,
    );
    return TutorResponseModel.fromJson(response as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> startDocumentSession(String documentId) async {
    final response = await _client.post(
      '${AppConfig.baseUrl}/tutor/document-session/$documentId',
    );
    return response as Map<String, dynamic>;
  }
}
