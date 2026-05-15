import threading
import time
import yaml
import os
import sys

def load_config():
    try:
        with open('config.yaml', 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("[WARN] config.yaml not found — using defaults.")
        return {}

def start_flask(config):
    from api.server import create_app
    app  = create_app()
    host = config.get('server', {}).get('host', '127.0.0.1')
    port = config.get('server', {}).get('port', 5000)
    app.run(host=host, port=port,
            debug=False, use_reloader=False)

if __name__ == "__main__":
    # Load config
    config = load_config()

    # Start Flask in background thread
    t = threading.Thread(
        target=start_flask, args=(config,), daemon=True)
    t.start()

    # Wait for Flask to start
    time.sleep(1.5)

    # Verify API is up before launching GUI
    import requests
    retries = 5
    for i in range(retries):
        try:
            r = requests.get(
                "http://localhost:5000/status", timeout=2)
            if r.status_code == 200:
                print("[OK] API is running — launching GUI...")
                break
        except Exception:
            print(f"[INFO] Waiting for API... ({i+1}/{retries})")
            time.sleep(1)
    else:
        print("[ERROR] API failed to start. Exiting.")
        sys.exit(1)

    # Launch GUI
    from gui.app import VAFApp
    app = VAFApp()
    app.mainloop()