from app import create_app


def test_create_app_returns_fastapi_app():
    app = create_app()
    paths = {route.path for route in app.routes}
    assert "/" in paths
    assert "/single-file/" in paths
    assert "/two-files/" in paths
