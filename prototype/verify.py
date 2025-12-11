import threading
import time
import webview
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

CALLBACK_PORT = 5000
callback_event = threading.Event()
response_data = {}

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/callback"):
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            
            # Extract relevant fields
            first = qs.get("fields[name-first][value]", [""])[0]
            last = qs.get("fields[name-last][value]", [""])[0]
            id_number = qs.get("fields[current-government-id][value][id]", [""])[0]
            status = qs.get("status", [""])[0]

            global response_data
            response_data = {
                "status": status,
                "name": f"{first} {last}".strip(),
                "id_number": id_number
            }

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            print("Callback received:", response_data)
            callback_event.set()
        else:
            self.send_response(404)
            self.end_headers()
            

def start_server():
    server = HTTPServer(("127.0.0.1", CALLBACK_PORT), CallbackHandler)
    server.serve_forever()

def run_verification(persona_link: str = None):
    """Start Persona verification and return the response dict"""
    global response_data, callback_event
    callback_event.clear()
    response_data = {}

    if not persona_link:
        persona_link = "" #Persona Hosted flow inquiry link

    redirect = f"http://127.0.0.1:{CALLBACK_PORT}/callback"
    persona_link += "&redirect-uri=" + redirect

    # Start callback server in background
    threading.Thread(target=start_server, daemon=True).start()

    # Create fullscreen webview
    window = webview.create_window("IDBallot Verification", persona_link, fullscreen=True)

    # Start a monitor thread that closes the window once callback is received
    def monitor_callback():
        while not callback_event.is_set():
            time.sleep(0.1)
        # Destroy webview window when callback is received
        try:
            webview.destroy_window(window)
        except Exception:
            pass

    threading.Thread(target=monitor_callback, daemon=True).start()

    # Start webview (blocks until window is destroyed)
    webview.start()

    # Return the response after window closes
    return response_data

# Optional: run standalone for testing
if __name__ == "__main__":
    resp = run_verification()
    print("Final response:", resp)
