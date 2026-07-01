import os


def build_info():
    return {
        "version": os.getenv("BUILD_VERSION", "2.5.0-dev"),
        "git_sha": os.getenv("GIT_SHA", "local"),
        "build_time": os.getenv("BUILD_TIME", ""),
        "service": "dxcon-api",
        "environment": os.getenv("APP_ENV", "development"),
    }
