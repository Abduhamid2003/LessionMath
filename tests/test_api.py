def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_and_plot(client):
    login = client.post(
        "/api/auth/login",
        data={"username": "student", "password": "student123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    plot = client.post(
        "/api/math/plot",
        json={"expression": "x**2", "x_min": -2, "x_max": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert plot.status_code == 200
    assert "x" in plot.json()


def test_achievements_me(client):
    login = client.post(
        "/api/auth/login",
        data={"username": "student", "password": "student123"},
    )
    token = login.json()["access_token"]
    r = client.get("/api/achievements/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
