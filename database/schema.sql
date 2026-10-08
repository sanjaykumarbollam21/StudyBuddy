-- =============================================================================
-- STUDY BUDDY - DATABASE SCHEMA (PostgreSQL / Supabase Compatible)
-- Normalized relational schema with pgvector support for RAG embeddings
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- -----------------------------------------------------------------------------
-- 1. USERS & AUTHENTICATION
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- -----------------------------------------------------------------------------
-- 2. USER PROFILES & ONBOARDING PREFERENCES
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    education_level VARCHAR(100),            -- e.g. High School, Undergraduate, Graduate
    target_goals TEXT,                       -- e.g. Prepare for finals, Master ML
    preferred_study_duration_mins INT DEFAULT 45,
    daily_available_mins INT DEFAULT 120,
    learning_style VARCHAR(50) DEFAULT 'visual_practical', -- visual, conceptual, practice_first
    current_knowledge_level VARCHAR(50) DEFAULT 'beginner', -- beginner, intermediate, advanced
    upcoming_exam_date DATE,
    avatar_url VARCHAR(500),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 3. USER SETTINGS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'system',      -- light, dark, system
    ai_provider VARCHAR(50) DEFAULT 'gemini',
    voice_speed FLOAT DEFAULT 1.0,
    voice_type VARCHAR(50) DEFAULT 'alloy',
    allow_email_notifications BOOLEAN DEFAULT TRUE,
    allow_study_reminders BOOLEAN DEFAULT TRUE,
    auto_generate_quizzes BOOLEAN DEFAULT TRUE,
    spaced_repetition_enabled BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 4. SUBJECTS & COLLECTIONS (Personal Knowledge Base organization)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'book',
    color_hex VARCHAR(10) DEFAULT '#4F46E5',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_subject UNIQUE(user_id, name)
);

CREATE TABLE IF NOT EXISTS collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 5. DOCUMENTS & DOCUMENT CHUNKS (RAG Pipeline)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    collection_id UUID REFERENCES collections(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),
    file_type VARCHAR(50) NOT NULL,          -- pdf, docx, txt, md
    file_size_bytes BIGINT NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_path VARCHAR(500),
    page_count INT DEFAULT 1,
    extracted_character_count INT DEFAULT 0,
    section_count INT DEFAULT 0,
    chunk_count INT DEFAULT 0,
    subject_name VARCHAR(150) DEFAULT 'General',
    collection_name VARCHAR(150) DEFAULT 'My Materials',
    status VARCHAR(50) DEFAULT 'ready',
    processing_status VARCHAR(50) DEFAULT 'ready', -- backward compatibility
    processing_stage VARCHAR(50) DEFAULT 'ready',
    progress INT DEFAULT 100,               -- 0 to 100
    processing_progress INT DEFAULT 100,
    error_message TEXT,
    
    -- Phase 3 Vector Embedding Metadata
    embedding_status VARCHAR(50) DEFAULT 'ready', -- pending, processing, ready, failed
    embedding_model VARCHAR(100) DEFAULT 'local-neural-hash-384',
    embedding_dimension INT DEFAULT 384,
    embedded_at TIMESTAMP WITH TIME ZONE,
    embedding_error TEXT,

    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_user ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_emb_status ON documents(embedding_status);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    page_number INT,
    section_title VARCHAR(255),
    character_start INT DEFAULT 0,
    character_end INT DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(768),                   -- vector dimensions (configurable per provider)
    embedding_model VARCHAR(100),
    embedded_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_user ON document_chunks(user_id);
CREATE INDEX IF NOT EXISTS idx_chunks_user_doc ON document_chunks(user_id, document_id);

-- -----------------------------------------------------------------------------
-- 6. TOPICS & KNOWLEDGE GRAPH (Relationships)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty VARCHAR(50) DEFAULT 'medium', -- beginner, intermediate, advanced
    estimated_mins INT DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Topic relationships for knowledge graph (prerequisite, related_to, depends_on)
CREATE TABLE IF NOT EXISTS topic_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    child_topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    relation_type VARCHAR(50) NOT NULL,      -- prerequisite, depends_on, related_to, extends
    CONSTRAINT uq_topic_relation UNIQUE(parent_topic_id, child_topic_id, relation_type)
);

-- -----------------------------------------------------------------------------
-- 7. LEARNING PATHS & ROADMAPS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    goal TEXT,
    source_type VARCHAR(50) DEFAULT 'user_materials', -- user_materials, web_research, hybrid
    total_steps INT DEFAULT 0,
    completed_steps INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'in_progress', -- not_started, in_progress, completed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_path_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    order_index INT NOT NULL,
    custom_title VARCHAR(255),
    description TEXT,
    estimated_minutes INT DEFAULT 30,
    status VARCHAR(50) DEFAULT 'locked',     -- locked, not_started, in_progress, practicing, needs_review, mastered
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 8. LESSONS & LESSON PROGRESS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS lessons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    learning_path_topic_id UUID REFERENCES learning_path_topics(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    key_takeaways JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lesson_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id UUID NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    is_completed BOOLEAN DEFAULT FALSE,
    time_spent_seconds INT DEFAULT 0,
    last_position INT DEFAULT 0,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_lesson UNIQUE(user_id, lesson_id)
);

-- -----------------------------------------------------------------------------
-- 9. QUIZZES, QUESTIONS, ANSWERS & EVALUATION
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quiz_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    lesson_id UUID REFERENCES lessons(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    total_questions INT NOT NULL,
    score_percentage FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'in_progress', -- in_progress, completed, abandoned
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_session_id UUID REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    question_type VARCHAR(50) NOT NULL,      -- mcq, multiple_select, true_false, fill_blank, short_answer, scenario
    prompt TEXT NOT NULL,
    options JSONB DEFAULT '[]'::jsonb,       -- For MCQ/multiple select
    correct_answer TEXT NOT NULL,
    explanation TEXT NOT NULL,
    difficulty VARCHAR(50) DEFAULT 'medium',
    learning_objective TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_session_id UUID REFERENCES quiz_sessions(id) ON DELETE CASCADE,
    student_response TEXT NOT NULL,
    is_correct BOOLEAN DEFAULT FALSE,
    score_awarded FLOAT DEFAULT 0.0,
    evaluation_feedback JSONB DEFAULT '{}'::jsonb, -- structured feedback: correctness, missing points, misconceptions
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 10. STUDENT MASTERY & ADAPTIVE LEARNING
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS student_mastery (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    mastery_percentage FLOAT DEFAULT 0.0,     -- 0 to 100
    times_practiced INT DEFAULT 0,
    consecutive_correct INT DEFAULT 0,
    last_evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    weak_areas JSONB DEFAULT '[]'::jsonb,
    CONSTRAINT uq_user_topic_mastery UNIQUE(user_id, topic_id)
);

-- -----------------------------------------------------------------------------
-- 11. STUDY SESSIONS & PLANS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    target_exam_date DATE,
    daily_target_hours FLOAT DEFAULT 2.0,
    schedule_data JSONB NOT NULL DEFAULT '[]'::jsonb, -- daily structured schedule items
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    duration_minutes INT NOT NULL,
    focus_topic VARCHAR(255),
    session_type VARCHAR(50) DEFAULT 'lesson', -- lesson, revision, quiz, practice, exam_prep
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 12. REVISION SYSTEM (Spaced Repetition)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS revision_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    last_studied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    repetition_interval_days INT DEFAULT 1,
    ease_factor FLOAT DEFAULT 2.5,           -- SuperMemo SM-2 algorithm multiplier
    repetition_count INT DEFAULT 0,
    next_review_date DATE NOT NULL,
    mastery_score FLOAT DEFAULT 0.0,
    is_due BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_revision_due ON revision_items(user_id, next_review_date);

-- -----------------------------------------------------------------------------
-- 13. EXAM SESSIONS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exam_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    total_duration_minutes INT NOT NULL,
    time_spent_seconds INT DEFAULT 0,
    total_questions INT NOT NULL,
    score_percentage FLOAT DEFAULT 0.0,
    detailed_report JSONB DEFAULT '{}'::jsonb, -- accuracy, time management, strong/weak topics, recommendations
    status VARCHAR(50) DEFAULT 'scheduled',    -- scheduled, in_progress, completed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- -----------------------------------------------------------------------------
-- 14. WEB RESEARCH SOURCES
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS research_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query VARCHAR(500) NOT NULL,
    title VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    snippet TEXT,
    authoritative_rating FLOAT DEFAULT 1.0,
    retrieval_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- 15. CHAT SESSIONS & MESSAGES (Conversational AI Tutor)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    title VARCHAR(255) DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,               -- user, assistant, system
    content TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,       -- Cited sources (document filename + page or external URL)
    suggested_actions JSONB DEFAULT '[]'::jsonb, -- Next action chips (e.g., Explain simpler, Quiz me)
    voice_audio_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

-- -----------------------------------------------------------------------------
-- 16. NOTIFICATIONS
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'reminder', -- reminder, revision_due, streak, exam_alert
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
