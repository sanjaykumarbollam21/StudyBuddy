import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Study Buddy" in data["service"]

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]

@pytest.mark.asyncio
async def test_student_signup_and_login_flow(client: AsyncClient):
    # 1. Sign up new student
    signup_payload = {
        "email": "student@studybuddy.io",
        "password": "SecurePassword123!",
        "full_name": "Test Student"
    }
    signup_res = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert signup_res.status_code == 201
    signup_data = signup_res.json()
    assert "access_token" in signup_data
    assert signup_data["user"]["email"] == "student@studybuddy.io"
    assert signup_data["user"]["full_name"] == "Test Student"
    token = signup_data["access_token"]

    # 2. Duplicate signup should be rejected with 400
    dup_res = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

    # 3. Login with correct credentials
    login_payload = {
        "email": "student@studybuddy.io",
        "password": "SecurePassword123!"
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["user"]["id"] == signup_data["user"]["id"]

    # 4. Login with invalid password should fail
    bad_login_res = await client.post("/api/v1/auth/login", json={
        "email": "student@studybuddy.io",
        "password": "WrongPassword!"
    })
    assert bad_login_res.status_code == 401

    # 5. Access protected /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "student@studybuddy.io"

    # 6. Access protected route without token fails with 401
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

@pytest.mark.asyncio
async def test_onboarding_profile_and_settings_update(client: AsyncClient):
    # Register student
    signup_payload = {
        "email": "onboarding@studybuddy.io",
        "password": "StrongPassword456!",
        "full_name": "Onboarding Student"
    }
    signup_res = await client.post("/api/v1/auth/signup", json=signup_payload)
    token = signup_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Update student profile (Onboarding survey)
    profile_update = {
        "education_level": "Undergraduate",
        "target_goals": "Prepare for Operating Systems semester exam",
        "preferred_study_duration_mins": 50,
        "daily_available_mins": 90,
        "learning_style": "conceptual",
        "current_knowledge_level": "intermediate"
    }
    profile_res = await client.put("/api/v1/users/profile", json=profile_update, headers=headers)
    assert profile_res.status_code == 200
    profile_data = profile_res.json()
    assert profile_data["profile"]["education_level"] == "Undergraduate"
    assert profile_data["profile"]["learning_style"] == "conceptual"
    assert profile_data["profile"]["daily_available_mins"] == 90

    # Update student settings
    settings_update = {
        "theme": "dark",
        "ai_provider": "gemini",
        "voice_speed": 1.2
    }
    settings_res = await client.put("/api/v1/users/settings", json=settings_update, headers=headers)
    assert settings_res.status_code == 200
    settings_data = settings_res.json()
    assert settings_data["settings"]["theme"] == "dark"
    assert settings_data["settings"]["voice_speed"] == 1.2

    # Check student notifications (welcome notification created on signup)
    notif_res = await client.get("/api/v1/users/notifications", headers=headers)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert len(notifs) >= 1
    assert "Welcome" in notifs[0]["title"]
