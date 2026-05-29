import os
import sys

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="lunaris-hello-backend")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "hello-backend",
        "version": "0.1.0",
        "pid": os.getpid(),
    }


def main() -> None:
    port = int(os.environ.get("LUNARIS_PORT", "0"))
    host = os.environ.get("LUNARIS_HOST", "127.0.0.1")
    if port == 0:
        # Allow CLI fallback for ad-hoc runs.
        for arg in sys.argv[1:]:
            if arg.startswith("--port="):
                port = int(arg.split("=", 1)[1])
    if port == 0:
        port = 8765
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
