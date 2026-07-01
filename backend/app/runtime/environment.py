import os


class Environment:
    PROVIDERS = ("render", "docker", "kubernetes", "local", "generic")

    @staticmethod
    def detect():
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            return "kubernetes"
        if os.getenv("RENDER"):
            return "render"
        if os.path.exists("/.dockerenv") or os.getenv("DXCON_DOCKER") == "1":
            return "docker"
        if os.getenv("DXCON_ENV_PROVIDER"):
            return os.getenv("DXCON_ENV_PROVIDER")
        return "local"

    @staticmethod
    def summary():
        return {
            "provider": Environment.detect(),
            "hostname": os.getenv("HOSTNAME"),
            "region": os.getenv("AWS_REGION") or os.getenv("RENDER_REGION") or os.getenv("DXCON_REGION"),
            "service": os.getenv("DXCON_SERVICE_NAME", "dxcon-api"),
            "namespace": os.getenv("KUBERNETES_NAMESPACE") or os.getenv("DXCON_NAMESPACE"),
        }
