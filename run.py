from app import create_app
import threading
import webview

app = create_app()


def run_flask_app() -> None:
    app.run(debug=False, port=5000, use_reloader=False)


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    webview.create_window("TT File Processor", "http://127.0.0.1:5000")
    webview.start()


