import json
import html

class HTMLGenerator:
    def __init__(self, workflows):
        self.workflows = workflows

    def generate(self, output_file):
        workflow_data = []
        
        for wf_idx, wf in enumerate(self.workflows):
            elements = []
            wf_id = f"wf_{wf_idx}"
            
            # Workflow node (parent)
            elements.append({
                'data': {
                    'id': wf_id,
                    'label': f"Workflow: {wf['name']}",
                    'type': 'workflow'
                }
            })

            for job in wf['jobs']:
                job_node_id = f"{wf_id}_{job['id']}"
                label = job['name']
                if job.get('uses'):
                    label += f"\nuses: {job['uses']}"
                if job.get('if'):
                    label += f"\nif: {job['if']}"
                
                elements.append({
                    'data': {
                        'id': job_node_id,
                        'parent': wf_id,
                        'label': label,
                        'type': 'job',
                        'condition': job.get('if')
                    }
                })

                # Steps and chronological edges
                prev_step_id = None
                for s_idx, step in enumerate(job['steps']):
                    step_id = f"{job_node_id}_step_{s_idx}"
                    step_label = step['name']
                    if step.get('uses'):
                        step_label += f"\nuses: {step['uses']}"
                    if step.get('if'):
                        step_label += f"\nif: {step['if']}"
                    
                    elements.append({
                        'data': {
                            'id': step_id,
                            'parent': job_node_id,
                            'label': step_label,
                            'type': 'step',
                            'condition': step.get('if')
                        }
                    })
                    
                    # Chronological edge between steps
                    if prev_step_id:
                        elements.append({
                            'data': {
                                'id': f"edge_{prev_step_id}_{step_id}",
                                'source': prev_step_id,
                                'target': step_id,
                                'type': 'chronology'
                            }
                        })
                    prev_step_id = step_id

                # Edges for 'needs'
                for need in job['needs']:
                    target_job_id = f"{wf_id}_{need}"
                    elements.append({
                        'data': {
                            'id': f"edge_{target_job_id}_{job_node_id}",
                            'source': target_job_id,
                            'target': job_node_id,
                            'type': 'dependency'
                        }
                    })
            
            workflow_data.append({
                'id': wf_id,
                'name': wf['name'],
                'filename': wf['filename'],
                'on': wf['on'],
                'on_full': wf['on_full'],
                'elements': elements,
                'raw_content': wf['raw_content']
            })

        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GitHub Actions Workflow Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/languages/yaml.min.js"></script>
    <style>
        :root {{
            --sidebar-width: 300px;
            --header-height: 60px;
            --primary-color: #24292e;
            --accent-color: #0366d6;
            --bg-color: #f6f8fa;
            --border-color: #e1e4e8;
        }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; margin: 0; display: flex; height: 100vh; overflow: hidden; color: #24292e; }}
        
        /* Sidebar */
        #sidebar {{
            width: var(--sidebar-width);
            background: #ffffff;
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        #sidebar .header {{
            padding: 20px;
            font-size: 1.2em;
            font-weight: bold;
            background: var(--primary-color);
            color: white;
        }}
        #sidebar .nav-list {{
            flex: 1;
            overflow-y: auto;
            padding: 10px 0;
        }}
        .nav-item {{
            padding: 12px 20px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 4px solid transparent;
            border-bottom: 1px solid #f0f0f0;
        }}
        .nav-item:hover {{ background: #f8f9fa; }}
        .nav-item.active {{
            background: #eef5ff;
            border-left-color: var(--accent-color);
        }}
        .nav-item .name {{
            display: block;
            font-weight: 600;
            font-size: 0.95em;
            margin-bottom: 4px;
        }}
        .nav-item .filename {{
            display: block;
            font-size: 0.8em;
            color: #6a737d;
            font-family: monospace;
        }}

        /* Main Content */
        #main {{
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-color);
            position: relative;
        }}
        #content-header {{
            height: var(--header-height);
            background: white;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            padding: 0 24px;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            z-index: 10;
        }}
        .tabs {{
            display: flex;
            background: #f1f1f1;
            padding: 4px;
            border-radius: 8px;
            gap: 4px;
        }}
        .tab {{
            padding: 6px 16px;
            cursor: pointer;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 600;
            transition: all 0.2s;
            color: #586069;
        }}
        .tab:hover {{ color: #24292e; }}
        .tab.active {{
            background: white;
            color: var(--accent-color);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        #view-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
        }}
        .view {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            display: none;
        }}
        .view.active {{ display: block; }}
        
        #cy {{ width: 100%; height: 100%; background: #f6f8fa; }}
        #code-view {{
            padding: 0;
            overflow: auto;
            background: white;
        }}
        pre {{ margin: 0; padding: 24px; }}
        code {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 13px; line-height: 1.5; }}

        .empty-state {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #6a737d;
        }}
        
        /* Metadata Panel */
        #metadata-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            width: 240px;
            background: white;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            z-index: 100;
            font-size: 0.85em;
            display: none;
        }}
        #metadata-panel h4 {{ margin: 0 0 10px 0; font-size: 1em; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        .meta-item {{ margin-bottom: 8px; }}
        .meta-label {{ font-weight: 600; color: #6a737d; display: block; margin-bottom: 2px; }}
        .meta-value {{ display: block; word-break: break-all; }}
        .tag {{
            display: inline-block;
            background: #e1f5fe;
            color: #01579b;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
        }}

        .legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            font-size: 0.8em;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            z-index: 5;
        }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 4px; }}
        .legend-color {{ width: 12px; height: 12px; margin-right: 8px; border-radius: 2px; }}
    </style>
</head>
<body>
    <div id="sidebar">
        <div class="header">Workflow Viewer</div>
        <div class="nav-list" id="nav-list"></div>
    </div>
    <div id="main">
        <div id="content-header">
            <h2 id="current-wf-title" style="margin:0; font-size: 1.1em; color: #24292e;">Select a workflow</h2>
            <div class="tabs">
                <div class="tab active" onclick="switchTab('graph')">Graph View</div>
                <div class="tab" onclick="switchTab('code')">YAML Source</div>
            </div>
        </div>
        <div id="view-container">
            <div id="graph-view" class="view active">
                <div id="metadata-panel">
                    <h4>Workflow Metadata</h4>
                    <div class="meta-item">
                        <span class="meta-label">Triggers (on):</span>
                        <div id="meta-triggers"></div>
                    </div>
                    <div class="meta-item" style="display:flex;gap:5px;">
                        <span class="meta-label">File: </span>
                        <span id="meta-filename" class="meta-value"></span>
                    </div>
                </div>
                <div id="cy"></div>
                <div class="legend">
                    <div class="legend-item"><div class="legend-color" style="background: #e1f5fe; border: 1px solid #01579b;"></div> Workflow</div>
                    <div class="legend-item"><div class="legend-color" style="background: #e8f5e9; border: 1px solid #2e7d32;"></div> Job</div>
                    <div class="legend-item"><div class="legend-color" style="background: #f5f5f5; border: 1px solid #9e9e9e;"></div> Step</div>
                </div>
            </div>
            <div id="code-view" class="view">
                <pre><code id="yaml-content" class="language-yaml"></code></pre>
            </div>
            <div id="no-selection" class="empty-state">
                <svg width="64" height="64" viewBox="0 0 16 16" fill="currentColor" style="opacity: 0.2; margin-bottom: 16px;">
                    <path d="M1.75 1.5a.25.25 0 00-.25.25v12.5c0 .138.112.25.25.25h12.5a.25.25 0 00.25-.25V1.75a.25.25 0 00-.25-.25H1.75zM0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v12.5A1.75 1.75 0 0114.25 16H1.75A1.75 1.75 0 010 14.25V1.75zm9.22 3.72a.75.75 0 000 1.06L10.19 7.5 9.22 8.47a.75.75 0 101.06 1.06l1.5-1.5a.75.75 0 000-1.06l-1.5-1.5a.75.75 0 00-1.06 0zM6.78 6.53a.75.75 0 00-1.06-1.06l-1.5 1.5a.75.75 0 000 1.06l1.5 1.5a.75.75 0 101.06-1.06L5.81 7.5l.97-.97z"></path>
                </svg>
                <p>Select a workflow from the sidebar to begin</p>
            </div>
        </div>
    </div>

    <script>
        const workflows = {json.dumps(workflow_data)};
        let currentWfId = null;
        let currentTab = 'graph';
        let cy = null;

        function initSidebar() {{
            const list = document.getElementById('nav-list');
            workflows.forEach(wf => {{
                const item = document.createElement('div');
                item.className = 'nav-item';
                item.id = 'nav-' + wf.id;
                item.innerHTML = `
                    <span class="name">${{wf.name}}</span>
                    <span class="filename">${{wf.filename}}</span>
                `;
                item.onclick = () => selectWorkflow(wf.id);
                list.appendChild(item);
            }});
        }}

        function selectWorkflow(id) {{
            if (currentWfId === id) return;
            
            if (currentWfId) {{
                document.getElementById('nav-' + currentWfId).classList.remove('active');
            }}
            document.getElementById('nav-' + id).classList.add('active');
            document.getElementById('no-selection').style.display = 'none';
            
            const wf = workflows.find(w => w.id === id);
            document.getElementById('current-wf-title').innerText = wf.name;
            document.getElementById('yaml-content').textContent = wf.raw_content;
            hljs.highlightElement(document.getElementById('yaml-content'));

            // Update Metadata
            document.getElementById('metadata-panel').style.display = 'block';
            document.getElementById('meta-filename').innerText = wf.filename;
            const triggersDiv = document.getElementById('meta-triggers');
            triggersDiv.innerHTML = '';
            wf.on.forEach(t => {{
                const span = document.createElement('span');
                span.className = 'tag';
                span.innerText = t;
                triggersDiv.appendChild(span);
            }});

            currentWfId = id;
            renderGraph(wf.elements);
            
            if (currentTab === 'code') {{
                switchTab('code');
            }}
        }}

        function switchTab(tab) {{
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            
            if (tab === 'graph') {{
                document.querySelector('.tab:nth-child(1)').classList.add('active');
                document.getElementById('graph-view').classList.add('active');
                if (cy) {{
                    cy.resize();
                    cy.fit();
                }}
            }} else {{
                document.querySelector('.tab:nth-child(2)').classList.add('active');
                document.getElementById('code-view').classList.add('active');
            }}
        }}

        function renderGraph(elements) {{
            if (cy) {{
                cy.destroy();
            }}
            
            cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: elements,
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'text-wrap': 'wrap',
                            'text-max-width': '150px',
                            'font-size': '10px',
                            'color': '#24292e'
                        }}
                    }},
                    {{
                        selector: 'node[type="workflow"]',
                        style: {{
                            'background-color': '#e1f5fe',
                            'border-width': 2,
                            'border-color': '#01579b',
                            'shape': 'rectangle',
                            'text-valign': 'top',
                            'padding': '40px'
                        }}
                    }},
                    {{
                        selector: 'node[type="job"]',
                        style: {{
                            'background-color': '#e8f5e9',
                            'border-width': 1,
                            'border-color': '#2e7d32',
                            'shape': 'round-rectangle',
                            'text-valign': 'top',
                            'padding': '20px'
                        }}
                    }},
                    {{
                        selector: 'node[type="step"]',
                        style: {{
                            'background-color': '#f5f5f5',
                            'border-width': 1,
                            'border-color': '#9e9e9e',
                            'shape': 'rectangle',
                            'font-size': '8px'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 2,
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier'
                        }}
                    }},
                    {{
                        selector: 'edge[type="dependency"]',
                        style: {{
                            'line-color': '#a1a8b0',
                            'target-arrow-color': '#a1a8b0',
                            'width': 3
                        }}
                    }},
                    {{
                        selector: 'edge[type="chronology"]',
                        style: {{
                            'line-color': '#ddd',
                            'target-arrow-color': '#ddd',
                            'width': 1.5,
                            'line-style': 'solid'
                        }}
                    }},
                    {{
                        selector: 'node[condition]',
                        style: {{
                            'border-style': 'dashed',
                            'border-width': 2
                        }}
                    }}
                ],
                layout: {{
                    name: 'dagre',
                    nodeSep: 100,
                    edgeSep: 50,
                    rankSep: 150,
                    rankDir: 'TB'
                }}
            }});
        }}

        initSidebar();
        if (workflows.length > 0) {{
            selectWorkflow(workflows[0].id);
        }}
    </script>
</body>
</html>
"""
        with open(output_file, 'w') as f:
            f.write(html_template)
