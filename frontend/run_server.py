import http.server
import socketserver
import webbrowser
import os
import sys

# Running Port
PORT = 8080

# Current Directory
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run():
    # Allow port reuse
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"\nFrontend is running at: {url}")
            print("Press Ctrl+C to stop server\n")
            
            # Open browser automatically
            webbrowser.open(url)
            
            # Run server
            httpd.serve_forever()
    except OSError as e:
        print(f"Error: {e}")
        print(f"Try changing the PORT in {__file__}")
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    run()
