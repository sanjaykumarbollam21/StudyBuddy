import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/search_model.dart';

class SearchApiService {
  final ApiClient _client = ApiClient();

  Future<SearchResponseModel> semanticSearch(
    String query, {
    int topK = 8,
    List<String>? documentIds,
    String? subject,
    String? collection,
  }) async {
    final body = <String, dynamic>{
      'query': query,
      'top_k': topK,
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

    final response = await _client.post(
      '${AppConfig.baseUrl}/search/semantic',
      body: body,
    );
    return SearchResponseModel.fromJson(response as Map<String, dynamic>);
  }

  Future<SearchResponseModel> hybridSearch(
    String query, {
    int topK = 8,
    List<String>? documentIds,
    String? subject,
    String? collection,
    double alpha = 0.7,
  }) async {
    final body = <String, dynamic>{
      'query': query,
      'top_k': topK,
      'alpha': alpha,
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

    final response = await _client.post(
      '${AppConfig.baseUrl}/search/hybrid',
      body: body,
    );
    return SearchResponseModel.fromJson(response as Map<String, dynamic>);
  }
}
