"""HTTP server for the in-memory URL shortener."""

import argparse
import errno
import html
import sys
from http.client import HTTPConnection, HTTPException
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import shortener
from src.linear_probing_table import LinearProbingTable

_STYLE = """
body { font: 16px system-ui, sans-serif; line-height: 1.5; margin: 0 auto;
       max-width: 900px; padding: 1rem; }
input[type=url] { box-sizing: border-box; max-width: 100%; padding: .7rem;
                  width: 36rem; }
button { cursor: pointer; margin-top: .5rem; padding: .7rem 1rem; }
a, code { overflow-wrap: anywhere; }
.bucket { border-top: 1px solid #ddd; padding: .65rem 0; }
.bucket-label { color: #555; font-family: monospace; }
.chain { align-items: flex-start; display: flex; flex-wrap: wrap; gap: .6rem;
         margin-top: .4rem; }
.node { border: 1px solid #bbb; border-radius: .35rem; min-width: 15rem;
        padding: .6rem; }
.node p { margin: .2rem 0; }
.arrow { font-size: 1.4rem; padding-top: .6rem; }
details { margin-top: .5rem; }
summary { cursor: pointer; }
@media (max-width: 600px) {
  body { padding: .75rem; }
  input[type=url] { width: 100%; }
  .node { min-width: 0; width: 100%; }
  .arrow { padding: 0; width: 100%; }
}
"""


class ShortenerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.partition("?")[0]
        if path == "/":
            self._send_html(200, "URL Shortener", self._home_content())
            return
        if path == "/table":
            self._send_html(200, "Hash table", self._table_content())
            return
        if path.startswith("/") and path.count("/") == 1:
            code = unquote(path[1:])
            try:
                url = shortener.expand(code)
            except KeyError:
                self._send_error_page(404, "Unknown short code")
                return

            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_error_page(404, "Page not found")

    def do_POST(self) -> None:
        if self.path.partition("?")[0] != "/shorten":
            self._send_error_page(404, "Page not found")
            return

        content_length = self.headers.get("Content-Length")
        try:
            body_length = int(content_length) if content_length is not None else -1
        except ValueError:
            self._send_error_page(400, "Invalid form submission")
            return
        if body_length < 0 or body_length > 8192:
            self._send_error_page(400, "Invalid form submission")
            return

        try:
            body = self.rfile.read(body_length).decode("utf-8")
            fields = parse_qsl(body, keep_blank_values=True, max_num_fields=16)
        except (UnicodeDecodeError, ValueError):
            self._send_error_page(400, "Invalid form submission")
            return

        url = None
        for name, value in fields:
            if name == "url":
                url = value
                break
        if url is None:
            self._send_error_page(400, "URL field is required")
            return

        try:
            code = shortener.shorten(url)
        except ValueError as error:
            self._send_error_page(400, str(error))
            return

        host = self.headers.get("Host", "localhost:8000")
        short_link = f"http://{host}/{code}"
        content = (
            '<main><h1>Your short link</h1>'
            f'<p><a href="/{html.escape(code, quote=True)}">'
            f"{html.escape(short_link)}</a></p>"
            '<p><a href="/">Shorten another URL</a></p></main>'
        )
        self._send_html(200, "Short URL", content)

    def _home_content(self) -> str:
        return (
            "<main><h1>URL Shortener</h1>"
            '<form action="/shorten" method="post">'
            '<label for="url">URL to shorten</label><br>'
            '<input id="url" name="url" type="url" maxlength="2048" required>'
            '<br><button type="submit">Shorten</button>'
            "</form><p><a href=\"/table\">Inspect hash table</a></p></main>"
        )

    def _table_content(self) -> str:
        table = shortener._URL_TO_CODE
        host = self.headers.get("Host", "localhost:8000")
        parts = [
            "<main><h1>Current hash table</h1>",
            '<p><a href="/">Back to URL shortener</a></p>',
        ]
        if isinstance(table, LinearProbingTable):
            for slot_index, url, code in table.iter_slots():
                parts.append(
                    f'<section class="bucket"><div class="bucket-label">'
                    f"Slot {slot_index}</div><div class=\"chain\">"
                )
                if url is None:
                    parts.append('<span class="empty">empty</span>')
                else:
                    steps = table.hash_steps(url)
                    step_items = []
                    for character, previous, value in steps:
                        calculation = (
                            f"h = ({previous} * 31 + ord({character!r})) "
                            f"% {table.capacity} = {value}"
                        )
                        step_items.append(
                            f"<li><code>{html.escape(calculation)}</code></li>"
                        )
                    home_index = steps[-1][2] if steps else 0
                    slots_inspected = (
                        (slot_index - home_index) % table.capacity + 1
                    )
                    short_link = f"/{code}"
                    parts.append(
                        '<article class="node">'
                        f"<p><strong>URL key:</strong> <code>{html.escape(url)}</code></p>"
                        f"<p><strong>Short code:</strong> <code>{html.escape(code)}</code></p>"
                        '<p><strong>Short link:</strong> '
                        f'<a href="/{html.escape(code, quote=True)}">'
                        f"{html.escape(short_link)}</a></p>"
                        f"<p>Home slot: {home_index}</p>"
                        f"<p>Slots inspected from home: {slots_inspected} "
                        f"(displacement: {slots_inspected - 1})</p>"
                        "<details><summary>Horner hash calculation</summary>"
                        f"<ol>{''.join(step_items)}</ol>"
                        f"<p>Initial slot index: {home_index}</p></details>"
                        "</article>"
                    )
                parts.append("</div></section>")
            parts.append("</main>")
            return "".join(parts)

        for bucket_index in range(table.capacity):
            entries = list(table.iter_bucket_items(bucket_index))
            parts.append(
                f'<section class="bucket"><div class="bucket-label">'
                f"Bucket {bucket_index}</div><div class=\"chain\">"
            )
            if not entries:
                parts.append('<span class="empty">empty</span>')
            for entry_index, (url, code) in enumerate(entries):
                if entry_index:
                    parts.append(
                        '<span class="arrow" aria-hidden="true">&rarr;</span>'
                    )

                steps = table.hash_steps(url)
                step_items = []
                for character, previous, value in steps:
                    calculation = (
                        f"h = ({previous} * 31 + ord({character!r})) "
                        f"% {table.capacity} = {value}"
                    )
                    step_items.append(f"<li><code>{html.escape(calculation)}</code></li>")
                final_hash = steps[-1][2] if steps else 0
                short_link = f"http://{host}/{code}"
                parts.append(
                    '<article class="node">'
                    f"<p><strong>URL key:</strong> <code>{html.escape(url)}</code></p>"
                    f"<p><strong>Short code:</strong> <code>{html.escape(code)}</code></p>"
                    '<p><strong>Short link:</strong> '
                    f'<a href="/{html.escape(code, quote=True)}">'
                    f"{html.escape(short_link)}</a></p>"
                    "<details><summary>Horner hash calculation</summary>"
                    f"<ol>{''.join(step_items)}</ol>"
                    f"<p>Final bucket index: {final_hash}</p></details>"
                    "</article>"
                )
            parts.append("</div></section>")
        parts.append("</main>")
        return "".join(parts)

    def _send_html(self, status: int, title: str, content: str) -> None:
        page = (
            "<!doctype html><html lang=\"en\"><head>"
            '<meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{html.escape(title)}</title>"
            f"<style>{_STYLE}</style></head><body>{content}</body></html>"
        )
        payload = page.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_error_page(self, status: int, message: str) -> None:
        content = (
            f"<main><h1>{status}</h1><p>{html.escape(message)}</p>"
            '<p><a href="/">Back</a></p></main>'
        )
        self._send_html(status, "Request error", content)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener HTTP server.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--table",
        choices=("chaining", "linear"),
        default="chaining",
        help="hash table implementation to use",
    )
    args = parser.parse_args()

    shortener.configure_table(args.table)
    server = _create_server(args.port)
    if server is None:
        return

    print(f"Serving URL shortener on port {server.server_port}")
    if args.port != 0 and server.server_port != args.port:
        print(f"Port {args.port} is already in use; using port {server.server_port}.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping URL shortener.")
    finally:
        server.server_close()


def _create_server(port: int) -> HTTPServer | None:
    try:
        return HTTPServer(("0.0.0.0", port), ShortenerHandler)
    except OSError as error:
        if error.errno != errno.EADDRINUSE:
            raise
        if _is_url_shortener_running(port):
            print(f"URL shortener is already running on port {port}")
            return None
        return HTTPServer(("0.0.0.0", 0), ShortenerHandler)


def _is_url_shortener_running(port: int) -> bool:
    connection = HTTPConnection("127.0.0.1", port, timeout=1)
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        body = response.read()
        return response.status == 200 and b"<h1>URL Shortener</h1>" in body
    except (OSError, HTTPException):
        return False
    finally:
        connection.close()


if __name__ == "__main__":
    main()
