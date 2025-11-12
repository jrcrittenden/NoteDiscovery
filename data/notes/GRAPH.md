# 🕸️ Graph Visualization

NoteDiscovery includes a powerful **graph visualization** feature that lets you see the relationships between your notes as an interactive network diagram.

## What is the Graph View?

The graph view displays all your notes as **nodes** (boxes) connected by **edges** (arrows) that represent wiki-style links between notes. This gives you a visual overview of how your knowledge base is interconnected.

## How to Access

Click the **🕸️ Graph** button at the bottom of the sidebar to open the graph visualization.

**Keyboard shortcut:**
- Press `Esc` to close the graph view

## Features

### Visual Navigation
- **Nodes** - Each note appears as a box labeled with the note name
- **Edges** - Arrows show links from one note to another (based on `[[wiki links]]`)
- **Current Note** - Your currently open note is highlighted in the accent color

### Interactive Controls

| Action | How To |
|--------|--------|
| **Navigate to a note** | Click on any node |
| **Move nodes** | Drag nodes to rearrange the layout |
| **Zoom** | Scroll wheel or pinch gesture |
| **Pan** | Click and drag the background |
| **Fit to view** | Double-click the background |
| **Navigation buttons** | Use the built-in navigation controls in the graph |

### Theme Integration

The graph automatically adapts to your current theme:
- Node colors match your theme's background and accent colors
- Text colors adjust for readability
- Border colors follow your theme palette
- Works perfectly with all 8 built-in themes

## Graph Statistics

The info panel in the bottom-left corner shows:
- **Total notes** - Number of nodes in your knowledge base
- **Total connections** - Number of links between notes

## Use Cases

### 1. **Knowledge Discovery**
Visualize how concepts connect across your notes. Find unexpected relationships and patterns.

### 2. **Content Organization**
Identify:
- **Hub notes** - Notes with many connections (central topics)
- **Orphan notes** - Isolated notes with no connections
- **Clusters** - Groups of related notes

### 3. **Navigation**
Jump between related notes visually instead of searching or browsing folders.

### 4. **Quality Control**
Spot:
- Broken links (edges pointing to non-existent notes)
- Under-connected areas that need more linking
- Over-connected notes that might need to be split

## Graph Physics

The graph uses a **force-directed layout** algorithm that:
- Positions connected notes closer together
- Spreads out unconnected notes
- Creates an organic, readable layout
- Animates smoothly as it stabilizes

You can manually adjust the layout by dragging nodes to your preferred positions.

## Tips

💡 **Create more links:** The more `[[wiki links]]` you add to your notes, the richer your graph becomes!

💡 **Use descriptive note names:** Clear note names make the graph easier to read.

💡 **Explore clusters:** Dense clusters indicate related topics that might benefit from a folder or tag system.

💡 **Double-click to reset:** If you zoom or pan too far, double-click the background to fit everything back into view.

## Technical Details

The graph visualization uses:
- **vis.js Network** - A high-performance JavaScript graph library
- **Barnes-Hut physics** - Efficient force-directed layout algorithm
- **Real-time data** - Graph updates when you click the button (based on current notes)
- **Theme-aware rendering** - CSS variables ensure perfect theme integration

---

**Ready to explore?** Click the 🕸️ Graph button and discover the hidden structure of your knowledge base!
