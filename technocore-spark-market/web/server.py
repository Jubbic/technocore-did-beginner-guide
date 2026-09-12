from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys

# Actual repository root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEB_DIR = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.market import build_market

HOST = "127.0.0.1"
PORT = 8000


class SparkMarketServer(BaseHTTPRequestHandler):

    def send_bytes(self, status, content_type, data):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/market":
            try:
                data = build_market()
                body = json.dumps(data, indent=2).encode("utf-8")
                self.send_bytes(200, "application/json; charset=utf-8", body)
            except Exception as error:
                body = json.dumps({
                    "error": str(error)
                }, indent=2).encode("utf-8")
                self.send_bytes(500, "application/json; charset=utf-8", body)
            return

        if self.path in ("/", "/index.html"):
            file_path = WEB_DIR / "index.html"

            if not file_path.exists():
                self.send_bytes(
                    404,
                    "text/plain; charset=utf-8",
                    b"index.html not found"
                )
                return

            data = file_path.read_bytes()
            self.send_bytes(200, "text/html; charset=utf-8", data)
            return

        if self.path.startswith("/"):
            relative = self.path.lstrip("/").split("?", 1)[0]
            file_path = WEB_DIR / relative

            if file_path.is_file():
                content_type = "application/octet-stream"

                if file_path.suffix == ".js":
                    content_type = "application/javascript; charset=utf-8"
                elif file_path.suffix == ".css":
                    content_type = "text/css; charset=utf-8"
                elif file_path.suffix == ".html":
                    content_type = "text/html; charset=utf-8"

                data = file_path.read_bytes()
                self.send_bytes(200, content_type, data)
                return

        self.send_bytes(
            404,
            "text/plain; charset=utf-8",
            b"Not found"
        )

    def log_message(self, format, *args):
        print(f"[HTTP] {self.address_string()} - {format % args}")


def main():
    server = ThreadingHTTPServer((HOST, PORT), SparkMarketServer)

    print("=" * 40)
    print("TECHNOCORE SPARK MARKET")
    print("=" * 40)
    print()
    print(f"Website: http://127.0.0.1:{PORT}")
    print(f"API:     http://127.0.0.1:{PORT}/api/market")
    print()
    print("Server is running.")
    print("Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
