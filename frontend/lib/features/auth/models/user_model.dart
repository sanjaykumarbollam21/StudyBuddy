class UserProfile {
  final String? educationLevel;
  final String? targetGoals;
  final int preferredStudyDurationMins;
  final int dailyAvailableMins;
  final String learningStyle;
  final String currentKnowledgeLevel;
  final String? bio;

  UserProfile({
    this.educationLevel,
    this.targetGoals,
    this.preferredStudyDurationMins = 45,
    this.dailyAvailableMins = 120,
    this.learningStyle = 'visual_practical',
    this.currentKnowledgeLevel = 'beginner',
    this.bio,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      educationLevel: json['education_level'] as String?,
      targetGoals: json['target_goals'] as String?,
      preferredStudyDurationMins: json['preferred_study_duration_mins'] as int? ?? 45,
      dailyAvailableMins: json['daily_available_mins'] as int? ?? 120,
      learningStyle: json['learning_style'] as String? ?? 'visual_practical',
      currentKnowledgeLevel: json['current_knowledge_level'] as String? ?? 'beginner',
      bio: json['bio'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'education_level': educationLevel,
      'target_goals': targetGoals,
      'preferred_study_duration_mins': preferredStudyDurationMins,
      'daily_available_mins': dailyAvailableMins,
      'learning_style': learningStyle,
      'current_knowledge_level': currentKnowledgeLevel,
      'bio': bio,
    };
  }
}

class UserSettings {
  final String theme;
  final String aiProvider;
  final double voiceSpeed;
  final String voiceType;
  final bool allowStudyReminders;
  final bool spacedRepetitionEnabled;

  UserSettings({
    this.theme = 'system',
    this.aiProvider = 'gemini',
    this.voiceSpeed = 1.0,
    this.voiceType = 'alloy',
    this.allowStudyReminders = true,
    this.spacedRepetitionEnabled = true,
  });

  factory UserSettings.fromJson(Map<String, dynamic> json) {
    return UserSettings(
      theme: json['theme'] as String? ?? 'system',
      aiProvider: json['ai_provider'] as String? ?? 'gemini',
      voiceSpeed: (json['voice_speed'] as num?)?.toDouble() ?? 1.0,
      voiceType: json['voice_type'] as String? ?? 'alloy',
      allowStudyReminders: json['allow_study_reminders'] as bool? ?? true,
      spacedRepetitionEnabled: json['spaced_repetition_enabled'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'theme': theme,
      'ai_provider': aiProvider,
      'voice_speed': voiceSpeed,
      'voice_type': voiceType,
      'allow_study_reminders': allowStudyReminders,
      'spaced_repetition_enabled': spacedRepetitionEnabled,
    };
  }
}

class UserModel {
  final String id;
  final String email;
  final String? fullName;
  final bool isActive;
  final bool isVerified;
  final UserProfile? profile;
  final UserSettings? settings;

  UserModel({
    required this.id,
    required this.email,
    this.fullName,
    this.isActive = true,
    this.isVerified = false,
    this.profile,
    this.settings,
  });

  String get displayName {
    if (fullName != null && fullName!.trim().isNotEmpty) {
      return fullName!;
    }
    return email.split('@').first;
  }

  bool get isOnboardingCompleted {
    return profile?.educationLevel != null && profile!.educationLevel!.isNotEmpty;
  }

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      isVerified: json['is_verified'] as bool? ?? false,
      profile: json['profile'] != null
          ? UserProfile.fromJson(json['profile'] as Map<String, dynamic>)
          : null,
      settings: json['settings'] != null
          ? UserSettings.fromJson(json['settings'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'is_active': isActive,
      'is_verified': isVerified,
      'profile': profile?.toJson(),
      'settings': settings?.toJson(),
    };
  }
}
