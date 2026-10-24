import '../../../core/config/app_config.dart';
import '../../../core/networking/api_client.dart';
import '../models/document_model.dart';

class DocumentApiService {
  final ApiClient _client = ApiClient();

  Future<List<DocumentItem>> listDocuments({
    String? status,
    String? subject,
    String? search,
  }) async {
    final queryParams = <String, String>{};
    if (status != null && status.isNotEmpty && status.toLowerCase() != 'all') {
      queryParams['status'] = status;
    }
    if (subject != null && subject.isNotEmpty) {
      queryParams['subject'] = subject;
    }
    if (search != null && search.isNotEmpty) {
      queryParams['search'] = search;
    }

    String url = AppConfig.documentsEndpoint;
    if (queryParams.isNotEmpty) {
      final query = queryParams.entries
          .map((e) => '${Uri.encodeComponent(e.key)}=${Uri.encodeComponent(e.value)}')
          .join('&');
      url += '?$query';
    }

    final response = await _client.get(url);
    if (response is List) {
      return response
          .map((item) => DocumentItem.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    return [];
  }

  Future<DocumentItem> uploadDocument({
    required List<int> fileBytes,
    required String filename,
    String? subjectName,
    String? collectionName,
  }) async {
    final fields = <String, String>{
      'subject_name': subjectName ?? 'General',
      'collection_name': collectionName ?? 'My Materials',
    };

    final response = await _client.uploadMultipart(
      '${AppConfig.documentsEndpoint}/upload',
      fieldName: 'file',
      fileBytes: fileBytes,
      filename: filename,
      fields: fields,
    );

    return DocumentItem.fromJson(response as Map<String, dynamic>);
  }

  Future<DocumentItem> getDocumentDetail(String documentId) async {
    final url = '${AppConfig.documentsEndpoint}/$documentId';
    final response = await _client.get(url);
    return DocumentItem.fromJson(response as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> getDocumentStatus(String documentId) async {
    final url = '${AppConfig.documentsEndpoint}/$documentId/status';
    final response = await _client.get(url);
    return response as Map<String, dynamic>;
  }

  Future<void> retryDocument(String documentId) async {
    final url = '${AppConfig.documentsEndpoint}/$documentId/retry';
    await _client.post(url);
  }

  Future<void> reindexDocument(String documentId) async {
    final url = '${AppConfig.documentsEndpoint}/$documentId/reindex';
    await _client.post(url);
  }

  Future<void> deleteDocument(String documentId) async {
    final url = '${AppConfig.documentsEndpoint}/$documentId';
    await _client.delete(url);
  }

  Future<void> bulkDeleteDocuments(List<String> documentIds) async {
    final url = '${AppConfig.documentsEndpoint}/bulk-delete';
    await _client.post(url, body: {'document_ids': documentIds});
  }

  Future<Map<String, dynamic>> learnFromDocument(String documentId) async {
    final url = '${AppConfig.baseUrl}/documents/learning/from-document/$documentId';
    final response = await _client.post(url);
    return response as Map<String, dynamic>;
  }
}
