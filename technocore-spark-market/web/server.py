from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys

# Make the project root available for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from api.market import build_market


WEB_DIR = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8000


class SparkMarketServer(BaseHTTPRequestHandler):

    def send_bytes(self, content, content_type, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):

        # API endpoint
        if self.path == "/api/market":

            try:
                data = build_market()

                content = json.dumps(
                    data,
                    indent=2
                ).encode("utf-8")

                self.send_bytes(
                    content,
                    "application/json; charset=utf-8"
                )

            except Exception as error:

                content = json.dumps(
                    {
                        "error": str(error)
                    }
                ).encode("utf-8")

                self.send_bytes(
                    content,
                    "application/json; charset=utf-8",
                    500
                )

            return

        # Homepage
        if self.path in ("/", "/index.html"):

            file_path = WEB_DIR / "index.html"

            if not file_path.exists():

                self.send_error(
                    404,
                    "index.html not found"
                )

                return

            content = file_path.read_bytes()

            self.send_bytes(
                content,
                "text/html; charset=utf-8"
            )

            return

        # Anything else
        self.send_error(404, "Not found")


def main():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        SparkMarketServer
    )

    print()
    print("========================================")
    print("TECHNOCORE SPARK MARKET")
    print("========================================")
    print()
    print(f"Website: http://{HOST}:{PORT}")
    print(f"API:     http://{HOST}:{PORT}/api/market")
    print()
    print("Server is running.")
    print("Press Ctrl+C to stop.")
    print()

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("Stopping server...")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()