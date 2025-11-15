# 🔌 Plugin System

NoteDiscovery includes a powerful plugin system that lets you extend functionality without modifying core code.

## How Plugins Work

Plugins are Python files that live in the `plugins/` directory. They use **event hooks** to react to actions in the app:

### Available Hooks

| Hook | When Triggered | Parameters | Can Modify |
|------|----------------|------------|------------|
| `on_note_create` | New note is created | `note_path`, `initial_content` | ✅ Yes (return modified content) |
| `on_note_save` | Note is being saved | `note_path`, `content` | ✅ Yes (return transformed content, or None) |
| `on_note_load` | Note is loaded from disk | `note_path`, `content` | ✅ Yes (return transformed content, or None) |
| `on_note_delete` | Note is deleted | `note_path` | ❌ No |
| `on_search` | Search is performed | `query`, `results` | ❌ No |
| `on_app_startup` | App starts up | None | ❌ No |

## ⚠️ Security Warning

**IMPORTANT:** Only install plugins from trusted sources.

Plugins have extensive access to your NoteDiscovery instance:
- **Backend access**: Full file system access, can read/write/delete notes
- **Frontend access**: Can inject JavaScript and CSS into your browser session
- **API access**: Can create custom API endpoints with no sandboxing
- **Data access**: Can access all note content, metadata, and user data

**Risks of malicious plugins:**
- Data theft (exfiltrate notes to external servers)
- Code injection (XSS attacks via frontend assets)
- File system manipulation (delete or corrupt notes)
- Privacy violations (track user activity, keylogging)

**Best practices:**
1. Only install plugins you have personally reviewed
2. Check plugin source code before enabling
3. Disable plugins you don't actively use
4. Monitor Docker logs for suspicious plugin activity
5. Keep plugin permissions in mind when exposing to the internet

## Creating a Plugin

### 1. Create a Python file

```bash
cd notediscovery/plugins
touch my_plugin.py
```

### 2. Define your plugin class

Every plugin must have a `Plugin` class with:
- `name` - Display name
- `version` - Version string
- `enabled` - Whether it's active (default: `True`)

### 3. Implement event hooks

Add methods for the events you want to handle.

## Basic Example: Note Logger

This simple plugin logs note activity to Docker logs (visible with `docker-compose logs -f`):

```python
"""
Note Logger Plugin
Logs all note operations to Docker logs for monitoring
"""

class Plugin:
    def __init__(self):
        self.name = "Note Logger"
        self.version = "1.0.0"
        self.enabled = True
    
    def on_note_save(self, note_path: str, content: str) -> str | None:
        """Log when a note is saved"""
        word_count = len(content.split())
        print(f"💾 Note saved: {note_path} ({word_count} words)")
        return None  # Don't modify content, just observe
    
    def on_note_delete(self, note_path: str):
        """Log when a note is deleted"""
        print(f"🗑️  Note deleted: {note_path}")
    
    def on_search(self, query: str, results: list):
        """Log search queries"""
        print(f"🔍 Search: '{query}' → {len(results)} results")
```

### How to see the logs

```bash
# View logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs -f notediscovery
```

## Activating Your Plugin

1. **Place the file** in `plugins/` directory
2. **Restart the app**: `docker-compose restart`
3. **Plugin auto-loads**: Plugins with `enabled = True` will automatically load

### Enable/Disable Plugins via API

Use the API to toggle plugins on/off:

**Linux/Mac:**
```bash
# Enable a plugin
curl -X POST http://localhost:8000/api/plugins/note_logger/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Disable a plugin
curl -X POST http://localhost:8000/api/plugins/note_logger/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

**Windows PowerShell:**
```powershell
# Enable a plugin
curl.exe -X POST http://localhost:8000/api/plugins/note_logger/toggle -H "Content-Type: application/json" -d "{\"enabled\": true}"

# Disable a plugin
curl.exe -X POST http://localhost:8000/api/plugins/note_logger/toggle -H "Content-Type: application/json" -d "{\"enabled\": false}"
```

**List all plugins (all platforms):**
```bash
curl http://localhost:8000/api/plugins
```

## Plugin State Persistence

Plugin states (enabled/disabled) are saved in `plugins/plugin_config.json` and persist between restarts.

## Advanced Plugin Features

### Frontend Assets (JavaScript & CSS)

Plugins can inject custom JavaScript and CSS into the frontend by implementing `get_frontend_assets()`:

```python
def get_frontend_assets(self) -> Dict[str, str]:
    """Return frontend assets to inject"""
    js_code = """
    // Your JavaScript code
    console.log('Plugin loaded!');
    """

    css_code = """
    /* Your CSS styles */
    .my-plugin-class {
        color: var(--accent-primary);
    }
    """

    return {'js': js_code, 'css': css_code}
```

**Use cases:**
- Add custom UI interactions
- Inject visualization libraries
- Apply custom styling
- Extend Alpine.js functionality

### Custom API Endpoints

Plugins can register custom API routes using FastAPI routers:

```python
from fastapi import APIRouter

def get_api_router(self) -> APIRouter:
    """Return custom API routes"""
    router = APIRouter()

    @router.get("/custom-endpoint")
    async def my_endpoint():
        return {"message": "Hello from plugin!"}

    @router.post("/process-data")
    async def process_data(data: dict):
        # Your processing logic
        return {"result": "processed"}

    return router
```

Routes are automatically prefixed with `/api/plugins/{plugin_name}/`.

**Example:** If your plugin is `my_plugin.py`, the endpoint becomes:
- `/api/plugins/my_plugin/custom-endpoint`
- `/api/plugins/my_plugin/process-data`

### UI Components

Plugins can inject UI components into specific locations:

```python
def get_ui_components(self) -> List[Dict]:
    """Return UI components to inject"""
    return [
        {
            'type': 'button',
            'location': 'sidebar_footer',
            'html': '<button onclick="myPluginFunction()">My Action</button>'
        }
    ]
```

## Built-in Plugins

### Enhanced Graph Visualization

**File:** `plugins/enhanced_graph.py`

Provides advanced graph visualization with:
- **Hierarchical data** - Top-level nodes with lazy-loaded children
- **Enhanced API endpoints** - `/api/plugins/enhanced_graph/graph/enhanced`
- **Lazy loading** - Load node children on demand via `/api/plugins/enhanced_graph/graph/node/{path}`

**API Usage:**
```bash
# Get hierarchical graph with depth=2
curl http://localhost:8000/api/plugins/enhanced_graph/graph/enhanced?depth=2

# Get children of a specific note
curl http://localhost:8000/api/plugins/enhanced_graph/graph/node/MyNote.md
```

**Features:**
- Hierarchical graph structure
- Top-level node detection (root notes, hub notes)
- Link count and child indicators
- Depth-based loading for performance

---

💡 **Tip:** Use `print()` statements in plugins to log to Docker logs for debugging and monitoring!

