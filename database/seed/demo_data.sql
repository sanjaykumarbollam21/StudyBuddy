-- =============================================================================
-- STUDY BUDDY - DEMO SEED DATA
-- Clearly marked sample data for Python, Machine Learning, OS, and DBMS
-- =============================================================================

-- 1. Demo User (Password: "StudyBuddy@123")
-- BCrypt hashed password for 'StudyBuddy@123'
INSERT INTO users (id, email, hashed_password, full_name, is_active, is_verified)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'student@studybuddy.ai',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Sanjay (Demo Student)',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- 2. Demo User Profile & Settings
INSERT INTO profiles (user_id, education_level, target_goals, preferred_study_duration_mins, daily_available_mins, learning_style, current_knowledge_level)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'Computer Science Undergraduate',
    'Ace Semester Exams in Operating Systems & Machine Learning',
    45,
    120,
    'visual_practical',
    'intermediate'
) ON CONFLICT (user_id) DO NOTHING;

INSERT INTO user_settings (user_id, theme, ai_provider, voice_speed, voice_type, allow_study_reminders, spaced_repetition_enabled)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'system',
    'gemini',
    1.0,
    'alloy',
    TRUE,
    TRUE
) ON CONFLICT (user_id) DO NOTHING;

-- 3. Demo Subjects
INSERT INTO subjects (id, user_id, name, description, icon, color_hex)
VALUES
    ('b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'Python Programming', 'Core Python concepts, data structures, and algorithms', 'code', '#3B82F6'),
    ('b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'Machine Learning', 'Supervised learning, deep learning, gradient descent', 'brain', '#8B5CF6'),
    ('b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'Operating Systems', 'Processes, memory management, threads, and synchronization', 'cpu', '#10B981'),
    ('b0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'Database Management Systems', 'Relational algebra, SQL, indexing, and normalization', 'database', '#F59E0B')
ON CONFLICT (id) DO NOTHING;

-- 4. Demo Topics
INSERT INTO topics (id, subject_id, title, description, difficulty, estimated_mins)
VALUES
    ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'Functions & Recursion', 'Base cases, call stack, and recursive thinking', 'medium', 40),
    ('c0000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000002', 'Gradient Descent Optimization', 'Cost functions, learning rates, and gradient convergence', 'hard', 50),
    ('c0000000-0000-0000-0000-000000000003', 'b0000000-0000-0000-0000-000000000003', 'Process Synchronization & Semaphores', 'Critical section problem, mutex locks, and deadlock avoidance', 'hard', 60),
    ('c0000000-0000-0000-0000-000000000004', 'b0000000-0000-0000-0000-000000000004', 'B-Tree Indexing & Query Optimization', 'Disk page lookups, tree height, and composite index usage', 'medium', 45)
ON CONFLICT (id) DO NOTHING;

-- 5. Demo Student Mastery Tracking
INSERT INTO student_mastery (user_id, topic_id, mastery_percentage, times_practiced, consecutive_correct, weak_areas)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 84.0, 5, 3, '["Memory stack overhead in deep recursion"]'::jsonb),
    ('a0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000002', 58.0, 3, 1, '["Choosing learning rate hyperparameters", "Saddle points"]'::jsonb),
    ('a0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000003', 42.0, 4, 0, '["Deadlock condition: Circular wait", "Dining Philosophers solution"]'::jsonb)
ON CONFLICT (user_id, topic_id) DO NOTHING;

-- 6. Demo Notifications
INSERT INTO notifications (user_id, title, message, notification_type, is_read)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Welcome to Study Buddy! 🚀', 'Your personal AI teacher is ready. Start by asking any question or exploring your roadmap.', 'reminder', FALSE),
    ('a0000000-0000-0000-0000-000000000001', 'Spaced Repetition Due ⏰', 'Time to review "Process Synchronization" to strengthen memory retention.', 'revision_due', FALSE);
