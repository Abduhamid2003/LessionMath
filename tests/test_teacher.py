def test_teacher_lesson_and_test_flow(client):
    login = client.post(
        "/api/auth/login",
        data={"username": "teacher", "password": "teacher123"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    lesson = client.post(
        "/api/teacher/lessons",
        json={
            "title_ru": "Тестовый урок",
            "content_ru": "Содержание урока",
            "category": "derivatives",
        },
        headers=headers,
    )
    assert lesson.status_code == 200
    lesson_id = lesson.json()["id"]

    test = client.post(
        "/api/teacher/tests",
        json={"title_ru": "Тест преподавателя", "category": "derivatives"},
        headers=headers,
    )
    assert test.status_code == 200
    test_id = test.json()["id"]

    q = client.post(
        f"/api/teacher/tests/{test_id}/questions",
        json={
            "question_ru": "2+2?",
            "options_ru": ["3", "4", "5"],
            "correct_answer": 1,
            "points": 10,
        },
        headers=headers,
    )
    assert q.status_code == 200

    detail = client.get(f"/api/teacher/tests/{test_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["questions"]) == 1

    client.delete(f"/api/teacher/lessons/{lesson_id}", headers=headers)
    client.delete(f"/api/teacher/tests/{test_id}", headers=headers)
