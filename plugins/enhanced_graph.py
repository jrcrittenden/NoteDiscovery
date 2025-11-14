"""
Enhanced Graph Visualization Plugin
Provides hierarchical graph view with hover-to-preview and click-to-pin interactions
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import yaml
from typing import Dict, List, Optional
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

class Plugin:
    def __init__(self):
        self.name = "Enhanced Graph Visualization"
        self.version = "1.0.0"
        self.enabled = True
        self.plugin_dir = None

    def get_api_router(self) -> APIRouter:
        """Return API router with enhanced graph endpoints"""
        router = APIRouter()

        # Load config
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        notes_dir = config['storage']['notes_dir']

        # Import utilities
        from backend.utils import get_all_notes, get_note_content, parse_wiki_links

        @router.get("/graph/enhanced")
        async def get_enhanced_graph(depth: int = 2):
            """
            Get hierarchical graph data with depth support.

            Args:
                depth: How many levels deep to load (default 2)

            Returns:
                {
                    nodes: [{id, label, level, link_count, has_children}],
                    edges: [{from, to, level}],
                    hierarchy: {node_id: {children: [], parent: str}}
                }
            """
            try:
                all_notes = get_all_notes(notes_dir)
                nodes_data = {}
                edges_data = []
                hierarchy = {}

                # First pass: collect all notes and their links
                for note in all_notes:
                    note_id = note['path']
                    content = get_note_content(notes_dir, note_id)

                    if content:
                        links = parse_wiki_links(content)
                    else:
                        links = []

                    nodes_data[note_id] = {
                        'id': note_id,
                        'label': note['name'],
                        'links': links,
                        'link_count': len(links),
                        'folder': note.get('folder', '')
                    }

                # Determine top-level nodes (root notes, hub notes, or notes with 0 incoming links)
                incoming_links = {note_id: 0 for note_id in nodes_data.keys()}
                for note_id, data in nodes_data.items():
                    for link in data['links']:
                        if link in incoming_links:
                            incoming_links[link] += 1

                # Top-level: root folder notes or notes with few incoming links (not heavily referenced)
                top_level_nodes = set()
                for note_id, incoming_count in incoming_links.items():
                    # Root notes or hub notes (3+ outgoing links) with few incoming
                    if nodes_data[note_id]['folder'] == '' or \
                       (nodes_data[note_id]['link_count'] >= 3 and incoming_count <= 2):
                        top_level_nodes.add(note_id)

                # If no top-level found, use root folder notes
                if not top_level_nodes:
                    top_level_nodes = {nid for nid, data in nodes_data.items() if data['folder'] == ''}

                # Build hierarchy
                for note_id in top_level_nodes:
                    hierarchy[note_id] = {
                        'children': nodes_data[note_id]['links'],
                        'parent': None,
                        'level': 0
                    }

                # Build nodes list with levels
                nodes = []
                for note_id in top_level_nodes:
                    nodes.append({
                        'id': note_id,
                        'label': nodes_data[note_id]['label'],
                        'level': 0,
                        'link_count': nodes_data[note_id]['link_count'],
                        'has_children': len(nodes_data[note_id]['links']) > 0
                    })

                # Build edges
                for note_id in top_level_nodes:
                    for link in nodes_data[note_id]['links']:
                        if link in nodes_data:
                            edges_data.append({
                                'from': note_id,
                                'to': link,
                                'level': 0
                            })

                            # If depth > 1, add first-level children
                            if depth > 1 and link not in top_level_nodes:
                                nodes.append({
                                    'id': link,
                                    'label': nodes_data[link]['label'],
                                    'level': 1,
                                    'link_count': nodes_data[link]['link_count'],
                                    'has_children': len(nodes_data[link]['links']) > 0
                                })

                                # Add to hierarchy
                                if link not in hierarchy:
                                    hierarchy[link] = {
                                        'children': nodes_data[link]['links'],
                                        'parent': note_id,
                                        'level': 1
                                    }

                return {
                    "nodes": nodes,
                    "edges": edges_data,
                    "hierarchy": hierarchy
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @router.get("/graph/node/{note_path:path}")
        async def get_node_children(note_path: str):
            """
            Get children of a specific node for lazy loading.

            Returns:
                {
                    nodes: [{id, label, level, link_count, has_children}],
                    edges: [{from, to}]
                }
            """
            try:
                content = get_note_content(notes_dir, note_path)
                if not content:
                    return {"nodes": [], "edges": []}

                links = parse_wiki_links(content)
                all_notes = get_all_notes(notes_dir)
                notes_map = {n['path']: n for n in all_notes}

                nodes = []
                edges = []

                for link in links:
                    if link in notes_map:
                        # Get link's links to determine if it has children
                        link_content = get_note_content(notes_dir, link)
                        child_links = parse_wiki_links(link_content) if link_content else []

                        nodes.append({
                            'id': link,
                            'label': notes_map[link]['name'],
                            'level': 1,  # Child level (relative)
                            'link_count': len(child_links),
                            'has_children': len(child_links) > 0
                        })

                        edges.append({
                            'from': note_path,
                            'to': link
                        })

                return {"nodes": nodes, "edges": edges}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        return router

    def get_frontend_assets(self) -> Dict[str, str]:
        """Return frontend JavaScript and CSS for enhanced graph"""

        js_code = """
// Enhanced Graph Visualization Plugin

// Add enhanced graph state to noteApp
document.addEventListener('alpine:init', () => {
    console.log('Enhanced Graph Plugin: Initializing...');

    // Extend Alpine app with enhanced graph functionality
    window.enhancedGraphReady = true;

    console.log('Enhanced Graph Plugin: Ready');
});

// Note: The main graph functionality is integrated via openGraph() in app.js
// This plugin adds enhanced API endpoints that can be used by the core graph feature
"""

        css_code = """
/* Enhanced Graph Plugin Styles */

/* Graph preview highlight */
.graph-node-previewed {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.6) !important;
    border-width: 3px !important;
}

/* Expandable node indicator */
.graph-node-expandable::after {
    content: '+';
    position: absolute;
    top: -8px;
    right: -8px;
    background: var(--accent-primary);
    color: white;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
}
"""

        return {'js': js_code, 'css': css_code}

