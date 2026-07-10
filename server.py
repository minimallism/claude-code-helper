from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import shutil
import sys
from pathlib import Path
from typing import TypedDict, Literal
from urllib.parse import parse_qs, urlparse


class ConfigInfo(TypedDict):
    path: Path
    name: str
    type: Literal['code', 'desktop']


ConfigMap = dict[str, ConfigInfo]


PORT = 8765
active_config: ConfigInfo | None = None


class ClaudeConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self.send_html()
        elif parsed_path.path == '/api/config':
            self.send_config()
        elif parsed_path.path == '/api/project':
            self.send_project_history()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/save':
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
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))


    def send_config(self):
        try:
            config = json.loads(active_config['path'].read_text(encoding='utf-8'))

            response = {
                'path': str(active_config['path']),
                'name': active_config['name'],
                'type': active_config['type'],
                'config': config,
                'project_sizes': {}
            }

            # Populate real disk sizes for CLI projects
            if active_config['type'] == 'code':
                sizes = {}
                for project_path in config.get('projects', {}):
                    project_dir = Path.home() / '.claude' / 'projects' / project_path.replace('/', '-')
                    if project_dir.is_dir():
                        sizes[project_path] = sum(file.stat().st_size for file in project_dir.rglob('*') if file.is_file())
                response['project_sizes'] = sizes

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))


    def send_project_history(self):
        try:
            query = parse_qs(urlparse(self.path).query)
            project_path = query.get('path', [''])[0]

            config = json.loads(active_config['path'].read_text(encoding='utf-8'))

            if project_path in config.get('projects', {}):
                project_data = config['projects'][project_path]

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Disposition', f'attachment; filename="project-history.json"')
                self.end_headers()
                self.wfile.write(json.dumps(project_data, indent=2, ensure_ascii=False).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error = {'error': str(e)}
            self.wfile.write(json.dumps(error).encode('utf-8'))


    def save_config(self):
        try:
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            new_config = json.loads(body.decode('utf-8'))

            path = active_config['path']

            # Clean up removed projects from disk (CLI only)
            if active_config['type'] == 'code' and path.exists():
                try:
                    old = json.loads(path.read_text(encoding='utf-8'))
                    removed = set(old.get('projects', {}).keys()) - set(new_config.get('projects', {}).keys())
                    for r in removed:
                        p = Path.home() / '.claude' / 'projects' / r.replace('/', '-')
                        if p.is_dir():
                            shutil.rmtree(p)
                except Exception:
                    pass

            # Create backup
            backup_path = path.parent / f"{path.stem}.backup{path.suffix}"
            if path.exists():
                shutil.copy2(path, backup_path)

            # Save
            path.write_text(json.dumps(new_config, indent=2, ensure_ascii=False), encoding='utf-8')

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'backup': str(backup_path)}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(error).encode('utf-8'))


    def log_message(self, format, *args):
        pass


def detect_configs() -> ConfigMap:
    configs = {}

    claude_code_path = Path.home() / '.claude.json'
    if claude_code_path.exists():
        configs['code'] = {
            'path': claude_code_path,
            'name': 'Claude Code (CLI)',
            'type': 'code'
        }


    if sys.platform == 'darwin':  # macOS
        claude_desktop_path = Path.home() / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
    elif sys.platform == 'win32':  # Windows
        claude_desktop_path = Path.home() / 'AppData' / 'Roaming' / 'Claude' / 'claude_desktop_config.json'
    else:  # Linux
        claude_desktop_path = Path.home() / '.config' / 'Claude' / 'claude_desktop_config.json'


    if claude_desktop_path.exists():
        configs['desktop'] = {
            'path': claude_desktop_path,
            'name': 'Claude Desktop',
            'type': 'desktop'
        }

    return configs


def select_config() -> ConfigInfo:
    """Interactive config selection"""
    configs = detect_configs()

    if not configs:
        print("❌ No Claude configuration files found!")
        print("💡 Please ensure Claude Code or Claude Desktop is installed and configured.")
        sys.exit(1)

    if len(configs) == 1:
        config_id = list(configs.keys())[0]
        return configs[config_id]


    print("\n🔍 Found multiple Claude configurations:\n")
    for i, (_, config) in enumerate(configs.items(), 1):
        path = config['path']
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  {i}. {config['name']}")
        print(f"     Path: {path}")
        print(f"     Size: {size_mb:.2f} MB\n")

    while True:
        try:
            choice = input(f"Select config (1-{len(configs)}) or press Enter for default [1]: ").strip()
            if not choice:
                choice = '1'
            choice_num = int(choice)
            if 1 <= choice_num <= len(configs):
                config_id = list(configs.keys())[choice_num - 1]
                return configs[config_id]
            else:
                print(f"Please enter a number between 1 and {len(configs)}")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\n👋 Cancelled")
            sys.exit(0)


def main():
    global active_config

    print("🚀 Claude Config Editor")
    print("   Universal editor for Claude Code & Claude Desktop\n")

    # Check for command line arg
    if len(sys.argv) > 1:
        config_type = sys.argv[1].lower()
        configs = detect_configs()
        if config_type in configs:
            active_config = configs[config_type]
        else:
            print(f"❌ Unknown config type: {config_type}")
            print(f"   Available: {', '.join(configs.keys())}")
            sys.exit(1)
    else:
        # Select config interactively
        active_config = select_config()

    print(f"\n✅ Active config: {active_config['name']}")
    print(f"📁 Path: {active_config['path']}")

    # Get file size
    size = active_config['path'].stat().st_size
    size_mb = size / (1024 * 1024)
    print(f"💾 Size: {size_mb:.2f} MB")

    print(f"\n🌐 Server: http://localhost:{PORT}")
    print(f"\n✨ Open your browser and navigate to the URL above")
    print(f"   Press Ctrl+C to stop\n")

    try:
        with HTTPServer(("", PORT), ClaudeConfigHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except OSError as e:
        if e.errno == 48:
            print(f"\n❌ Port {PORT} is already in use.")
            print(f"   Try closing any existing instances or use a different port.")
            sys.exit(1)
        else:
            raise


if __name__ == '__main__':
    main()