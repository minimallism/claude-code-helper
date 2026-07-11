from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import shutil
import sys
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse


class ConfigInfo(TypedDict):
    path: Path


PORT = 8765
active_config: ConfigInfo | None = None


def cache_dir_name(project_path: str) -> str:
    """Claude Code 缓存目录编码：仅 ASCII 字母数字保留，其他字符（含中文/下划线/斜杠）换成 -"""
    result = []
    for char in project_path:
        if 'a' <= char <= 'z' or 'A' <= char <= 'Z' or '0' <= char <= '9':
            result.append(char)
        else:
            result.append('-')
    return ''.join(result)


class ClaudeConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self.send_html()
        elif parsed_path.path == '/api/config':
            self.send_config()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/save':
            self.save_config()
        else:
            self.send_response(404)
            self.end_headers()


    def send_html(self):
        html_path = Path(__file__).parent / 'index.html'
        try:
            html = html_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            html = '<h1>Error: index.html not found</h1>'

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        try:
            self.wfile.write(html.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError):
            pass


    def send_config(self):
        try:
            config = json.loads(active_config['path'].read_text(encoding='utf-8'))

            response = {
                'path': str(active_config['path']),
                'config': config,
                'config_size': active_config['path'].stat().st_size,
                'project_sizes': {}
            }

            # 统计 ~/.claude/projects 下各项目缓存目录的磁盘占用
            sizes = {}
            for project_path in config.get('projects', {}):
                if not project_path:
                    continue
                project_dir = Path.home() / '.claude' / 'projects' / cache_dir_name(project_path)
                if project_dir.is_dir():
                    sizes[project_path] = sum(file.stat().st_size for file in project_dir.rglob('*') if file.is_file())
            response['project_sizes'] = sizes

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                pass
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                pass


    def save_config(self):
        try:
            content_length = self.headers.get('Content-Length', '')
            if not content_length:
                raise ValueError('Missing Content-Length header')
            content_length = int(content_length)
            body = self.rfile.read(content_length)
            new_config = json.loads(body.decode('utf-8'))

            path = active_config['path']

            # 清理已删除项目的磁盘缓存
            try:
                old = json.loads(path.read_text(encoding='utf-8'))
                removed = set(old.get('projects', {}).keys()) - set(new_config.get('projects', {}).keys())
                for r in removed:
                    if not r:
                        continue
                    p = Path.home() / '.claude' / 'projects' / cache_dir_name(r)
                    if p.is_dir():
                        shutil.rmtree(p)
            except Exception:
                pass

            # Save
            path.write_text(json.dumps(new_config, indent=2, ensure_ascii=False), encoding='utf-8')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                pass
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error = {'success': False, 'error': str(e)}
            try:
                self.wfile.write(json.dumps(error).encode('utf-8'))
            except (BrokenPipeError, ConnectionResetError):
                pass


    def log_message(self, format, *args):
        pass


def detect_config() -> ConfigInfo | None:
    claude_code_path = Path.home() / '.claude.json'
    if claude_code_path.exists():
        return {
            'path': claude_code_path,
        }
    return None


def main():
    global active_config

    print("🚀 Claude Code History Cleaner")
    print("   可视化项目空间占用 · 批量清理闲置历史\n")

    active_config = detect_config()
    if not active_config:
        print("❌ No Claude configuration files found!")
        print("💡 Please ensure Claude Code is installed and configured.")
        sys.exit(1)

    print(f"\n🟢 Config: {active_config['path']}")

    # Get file size
    size = active_config['path'].stat().st_size
    size_mb = size / (1000 * 1000)
    print(f"📦 Size: {size_mb:.2f} MB")

    print(f"\n🌐 Server: http://localhost:{PORT}")
    print(f"\n✨ Open your browser and navigate to the URL above")
    print(f"   Press Ctrl+C to stop\n")

    try:
        with HTTPServer(("localhost", PORT), ClaudeConfigHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except OSError as e:
        if e.errno in (48, 98, 10048):  # 48 macOS, 98 Linux, 10048 Windows EADDRINUSE
            print(f"\n❌ Port {PORT} is already in use.")
            print(f"   Try closing any existing instances or use a different port.")
            sys.exit(1)
        else:
            raise


if __name__ == '__main__':
    main()
