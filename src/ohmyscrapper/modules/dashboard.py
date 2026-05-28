from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import ohmyscrapper.models.urls_manager as urls_manager


def _records(dataframe):
    return dataframe.to_dict("records")


def _text(value, default=""):
    if value is None or value != value:
        return default
    return str(value)


def _int(value, default=0):
    try:
        if value is None or value != value:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _timestamp(value):
    seconds = _int(value, default=0)
    if seconds <= 0:
        return "-"
    return datetime.fromtimestamp(seconds, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def _progress(run):
    total = _int(run.get("total_urls"))
    completed = _int(run.get("completed_count"))
    skipped = _int(run.get("skipped_count"))
    failed = _int(run.get("failure_count"))
    processed = completed + skipped + failed
    percentage = 0
    if total > 0:
        percentage = min(100, int((processed / total) * 100))
    return {
        "total": total,
        "completed": completed,
        "skipped": skipped,
        "failed": failed,
        "processed": processed,
        "percentage": percentage,
    }


def get_dashboard_runs(limit=20):
    return _records(urls_manager.get_scraping_runs(limit=limit))


def get_dashboard_run(run_id):
    run = urls_manager.get_scraping_run(run_id)
    if len(run) == 0:
        return None
    return run.iloc[0].to_dict()


def get_dashboard_errors(limit=10):
    return _records(urls_manager.get_recent_url_errors(limit=limit))


def _page(title, body):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - OhMyScrapper</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Arial, sans-serif; }}
    body {{ margin: 0; background: #f6f7f9; color: #20242a; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    header {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 20px; }}
    h1 {{ margin: 0; font-size: 28px; }}
    h2 {{ margin: 28px 0 12px; font-size: 20px; }}
    a {{ color: #0b63ce; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d8dde6; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e4e8ef; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; font-size: 13px; text-transform: uppercase; }}
    .status {{ font-weight: 700; }}
    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
    .metric {{ background: #fff; border: 1px solid #d8dde6; padding: 14px; }}
    .metric strong {{ display: block; font-size: 24px; margin-top: 4px; }}
    .empty {{ padding: 18px; background: #fff; border: 1px solid #d8dde6; }}
    .error {{ color: #9f1d20; }}
    @media (prefers-color-scheme: dark) {{
      body {{ background: #15171a; color: #f1f3f5; }}
      table, .metric, .empty {{ background: #20242a; border-color: #39404a; }}
      th {{ background: #2b3139; }}
      th, td {{ border-bottom-color: #39404a; }}
      a {{ color: #7ab7ff; }}
    }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>"""


def render_runs_page(limit=20):
    runs = get_dashboard_runs(limit=limit)
    if len(runs) == 0:
        rows = '<div class="empty">No scraping runs found.</div>'
    else:
        run_rows = []
        for run in runs:
            progress = _progress(run)
            run_rows.append(
                "<tr>"
                f"<td><a href=\"/runs/{_int(run.get('id'))}\">#{_int(run.get('id'))}</a></td>"
                f"<td>{escape(_text(run.get('command')))}</td>"
                f"<td class=\"status\">{escape(_text(run.get('status')))}</td>"
                f"<td>{progress['processed']}/{progress['total']} ({progress['percentage']}%)</td>"
                f"<td>{progress['completed']}</td>"
                f"<td>{progress['skipped']}</td>"
                f"<td>{progress['failed']}</td>"
                f"<td>{_timestamp(run.get('started_at'))}</td>"
                f"<td>{_timestamp(run.get('finished_at'))}</td>"
                "</tr>"
            )
        rows = (
            "<table><thead><tr><th>Run</th><th>Command</th><th>Status</th>"
            "<th>Progress</th><th>Completed</th><th>Skipped</th><th>Failed</th>"
            "<th>Started</th><th>Finished</th></tr></thead><tbody>"
            + "".join(run_rows)
            + "</tbody></table>"
        )

    return _page(
        "Scraping Runs",
        f"<header><h1>Scraping Runs</h1></header><h2>Recent Runs</h2>{rows}",
    )


def render_run_detail_page(run_id, error_limit=10):
    run = get_dashboard_run(run_id)
    if run is None:
        return _page(
            "Run Not Found",
            '<header><h1>Run Not Found</h1><a href="/">Recent runs</a></header>'
            f'<div class="empty">Run #{escape(str(run_id))} was not found.</div>',
        )

    progress = _progress(run)
    errors = get_dashboard_errors(limit=error_limit)
    if len(errors) == 0:
        error_rows = '<div class="empty">No recent URL errors found.</div>'
    else:
        rows = []
        for error in errors:
            rows.append(
                "<tr>"
                f"<td>{escape(_text(error.get('url')))}</td>"
                f"<td>{escape(_text(error.get('url_type'), '-'))}</td>"
                f"<td class=\"error\">{escape(_text(error.get('error')))}</td>"
                f"<td>{_timestamp(error.get('last_touch') or error.get('created_at'))}</td>"
                "</tr>"
            )
        error_rows = (
            "<table><thead><tr><th>URL</th><th>Type</th><th>Error</th>"
            "<th>Recorded</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )

    body = f"""
<header><h1>Run #{_int(run.get('id'))}</h1><a href="/">Recent runs</a></header>
<section class="summary">
  <div class="metric">Status<strong>{escape(_text(run.get('status')))}</strong></div>
  <div class="metric">Progress<strong>{progress['processed']}/{progress['total']}</strong></div>
  <div class="metric">Completed<strong>{progress['completed']}</strong></div>
  <div class="metric">Skipped<strong>{progress['skipped']}</strong></div>
  <div class="metric">Failed<strong>{progress['failed']}</strong></div>
</section>
<h2>Run Details</h2>
<table><tbody>
  <tr><th>Command</th><td>{escape(_text(run.get('command')))}</td></tr>
  <tr><th>Started</th><td>{_timestamp(run.get('started_at'))}</td></tr>
  <tr><th>Updated</th><td>{_timestamp(run.get('updated_at'))}</td></tr>
  <tr><th>Finished</th><td>{_timestamp(run.get('finished_at'))}</td></tr>
  <tr><th>Run error</th><td class="error">{escape(_text(run.get('error'), '-'))}</td></tr>
</tbody></table>
<h2>Recent Scrape Errors</h2>
{error_rows}
"""
    return _page(f"Run #{_int(run.get('id'))}", body)


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        limit = _int(query.get("limit", [20])[0], default=20)

        status = 200
        if path == "/":
            body = render_runs_page(limit=limit)
        elif path.startswith("/runs/"):
            run_id = path.split("/")[-1]
            body = render_run_detail_page(run_id)
            if "Run Not Found" in body:
                status = 404
        else:
            status = 404
            body = _page(
                "Not Found",
                '<header><h1>Not Found</h1><a href="/">Recent runs</a></header>',
            )

        content = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        return


def start_dashboard(host="127.0.0.1", port=8765):
    server = ThreadingHTTPServer((host, int(port)), DashboardHandler)
    print(f"-- dashboard running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n-- dashboard stopped")
    finally:
        server.server_close()
