from app import create_app
import threading
import webview
import uvicorn

app = create_app()


def run_fastapi_app() -> None:
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="warning")


if __name__ == "__main__":
    fastapi_thread = threading.Thread(target=run_fastapi_app, daemon=True)
    fastapi_thread.start()
    webview.create_window("TT File Processor", "http://127.0.0.1:5000")
    webview.start()

    
