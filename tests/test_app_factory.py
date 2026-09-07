from app import create_app


def test_create_app_returns_flask_app():
    app = create_app()
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/" in rules
    assert "/single-file/" in rules
    assert "/two-files/" in rules
