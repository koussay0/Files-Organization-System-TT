from app import create_app
import threading
import time
import urllib.request
import urllib.error
import webview

app = create_app()


def run_flask_app() -> None:
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    for _ in range(50):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000", timeout=0.2)
            break
        except (ConnectionRefusedError, TimeoutError, urllib.error.URLError):
            time.sleep(0.1)
    webview.create_window("TT File Processor", "http://127.0.0.1:5000")
    webview.start()

