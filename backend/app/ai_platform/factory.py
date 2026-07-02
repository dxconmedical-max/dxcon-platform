def init_ai_platform(app):
    app.extensions.setdefault("ai_platform", {"initialized": True})
    return app.extensions["ai_platform"]
