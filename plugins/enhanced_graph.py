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
// Provides hover-to-preview and click-to-pin functionality

(function() {
    console.log('Enhanced Graph Plugin: Initializing...');

    // Wait for Alpine to be ready
    document.addEventListener('alpine:init', () => {
        // Store reference to the Alpine app data
        window.enhancedGraphPlugin = {
            enabled: true,
            cache: new Map(), // Cache for node children

            // Fetch children for a node
            async fetchNodeChildren(nodeId) {
                if (this.cache.has(nodeId)) {
                    return this.cache.get(nodeId);
                }

                try {
                    const response = await fetch(`/api/plugins/enhanced_graph/graph/node/${nodeId}`);
                    if (!response.ok) throw new Error('Failed to fetch node children');

                    const data = await response.json();
                    this.cache.set(nodeId, data);
                    return data;
                } catch (error) {
                    console.error('Enhanced Graph Plugin: Failed to fetch children for', nodeId, error);
                    return { nodes: [], edges: [] };
                }
            },

            // Add nodes to the graph
            addNodesToGraph(app, newNodes, newEdges, temporary = false) {
                if (!app.graphNetwork) return;

                const nodes = app.graphNetwork.body.data.nodes;
                const edges = app.graphNetwork.body.data.edges;

                // Get theme colors
                const styles = getComputedStyle(document.documentElement);
                const bgSecondary = styles.getPropertyValue('--bg-secondary').trim() || '#f3f4f6';
                const textPrimary = styles.getPropertyValue('--text-primary').trim() || '#111827';
                const textSecondary = styles.getPropertyValue('--text-secondary').trim() || '#6b7280';
                const accentPrimary = styles.getPropertyValue('--accent-primary').trim() || '#3b82f6';
                const borderPrimary = styles.getPropertyValue('--border-primary').trim() || '#e5e7eb';

                // Add new nodes
                newNodes.forEach(node => {
                    if (!nodes.get(node.id)) {
                        nodes.add({
                            id: node.id,
                            label: node.label,
                            title: node.label,
                            color: {
                                background: temporary ? 'rgba(243, 244, 246, 0.6)' : bgSecondary,
                                border: temporary ? textSecondary : borderPrimary,
                                highlight: {
                                    background: accentPrimary,
                                    border: accentPrimary
                                },
                                hover: {
                                    background: accentPrimary,
                                    border: accentPrimary
                                }
                            },
                            font: {
                                color: textPrimary,
                                size: temporary ? 12 : 14,
                                face: 'system-ui, -apple-system, sans-serif'
                            },
                            borderWidth: temporary ? 1 : 2,
                            borderWidthSelected: 3,
                            shape: 'box',
                            margin: temporary ? 5 : 10,
                            opacity: temporary ? 0.7 : 1,
                            widthConstraint: {
                                maximum: 200
                            },
                            _temporary: temporary,
                            _hasChildren: node.has_children || false
                        });

                        // Track temporary nodes
                        if (temporary) {
                            app.temporaryNodes.add(node.id);
                        }
                    }
                });

                // Add new edges
                newEdges.forEach(edge => {
                    const edgeId = `${edge.from}->${edge.to}`;
                    if (!edges.get(edgeId)) {
                        edges.add({
                            id: edgeId,
                            from: edge.from,
                            to: edge.to,
                            arrows: 'to',
                            color: {
                                color: textSecondary,
                                highlight: accentPrimary,
                                hover: accentPrimary
                            },
                            smooth: {
                                type: 'curvedCW',
                                roundness: 0.2
                            },
                            width: temporary ? 1 : 1.5,
                            dashes: temporary ? [5, 5] : false,
                            _temporary: temporary
                        });
                    }
                });
            },

            // Remove temporary nodes
            removeTemporaryNodes(app) {
                if (!app.graphNetwork) return;

                const nodes = app.graphNetwork.body.data.nodes;
                const edges = app.graphNetwork.body.data.edges;

                // Remove temporary nodes
                const tempNodes = Array.from(app.temporaryNodes);
                tempNodes.forEach(nodeId => {
                    const node = nodes.get(nodeId);
                    if (node && node._temporary && !app.expandedNodes.has(nodeId)) {
                        nodes.remove(nodeId);
                        app.temporaryNodes.delete(nodeId);
                    }
                });

                // Remove temporary edges
                edges.get().forEach(edge => {
                    if (edge._temporary && !app.expandedNodes.has(edge.from)) {
                        edges.remove(edge.id);
                    }
                });
            }
        };

        console.log('Enhanced Graph Plugin: Ready');
    });

    // Override the showTemporaryChildren method
    setTimeout(() => {
        const checkApp = setInterval(() => {
            const app = window.Alpine?.store?.noteApp || document.querySelector('[x-data]')?.__x?.$data;
            if (app && window.enhancedGraphPlugin) {
                // Override showTemporaryChildren
                app.showTemporaryChildren = async function(nodeId) {
                    const data = await window.enhancedGraphPlugin.fetchNodeChildren(nodeId);
                    if (data.nodes.length > 0) {
                        window.enhancedGraphPlugin.addNodesToGraph(this, data.nodes, data.edges, true);
                    }
                };

                // Override hideTemporaryChildren
                app.hideTemporaryChildren = function(nodeId) {
                    window.enhancedGraphPlugin.removeTemporaryNodes(this);
                };

                // Add click-to-pin functionality
                const originalClickHandler = app.graphNetwork?.on;
                if (app.graphNetwork) {
                    app.graphNetwork.on('click', async (params) => {
                        if (params.nodes.length > 0) {
                            const nodeId = params.nodes[0];

                            // If node is already expanded, collapse it
                            if (app.expandedNodes.has(nodeId)) {
                                app.expandedNodes.delete(nodeId);
                                window.enhancedGraphPlugin.removeTemporaryNodes(app);
                            } else {
                                // Expand node (pin children)
                                const data = await window.enhancedGraphPlugin.fetchNodeChildren(nodeId);
                                if (data.nodes.length > 0) {
                                    window.enhancedGraphPlugin.addNodesToGraph(app, data.nodes, data.edges, false);
                                    app.expandedNodes.add(nodeId);
                                }
                            }

                            // Also show preview
                            app.previewGraphNode(nodeId);
                        }
                    });
                }

                clearInterval(checkApp);
            }
        }, 100);
    }, 500);
})();
"""

        css_code = """
/* Enhanced Graph Plugin Styles */

/* Graph preview highlight */
.graph-node-previewed {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.6) !important;
    border-width: 3px !important;
}

/* Temporary nodes (hover preview) */
.vis-network .vis-node.temporary {
    opacity: 0.7;
    transition: opacity 0.3s ease;
}

/* Smooth transitions for graph changes */
.vis-network {
    transition: all 0.3s ease;
}

/* Preview pane animations */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.graph-preview-pane {
    animation: slideIn 0.3s ease-out;
}

/* Resize handle hover effect */
.graph-preview-resize-handle:hover {
    background-color: var(--accent-primary) !important;
    transition: background-color 0.2s ease;
}
"""

        return {'js': js_code, 'css': css_code}

