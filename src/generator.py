import json

class HTMLGenerator:
    def __init__(self, workflows):
        self.workflows = workflows

    def generate(self, output_file):
        elements = []
        
        for wf_idx, wf in enumerate(self.workflows):
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
                if job['uses']:
                    label += f"\nuses : {job['uses']}"
                if job['if']:
                    label += f"\n[if: {job['if']}]"
                # Job node
                elements.append({
                    'data': {
                        'id': job_node_id,
                        'parent': wf_id,
                        'label': label,
                        'type': 'job',
                        'condition': job['if']
                    }
                })

                # Steps as child nodes or metadata? Let's add them as nested nodes for "inclusions"
                for s_idx, step in enumerate(job['steps']):
                    step_id = f"{job_node_id}_step_{s_idx}"
                    step_label = step['name']
                    if step['uses']:
                        step_label += f"\nuses : {step['uses']}"
                    if job['if']:
                        label += f"\nif : {job['if']}"
                    
                    elements.append({
                        'data': {
                            'id': step_id,
                            'parent': job_node_id,
                            'label': step_label,
                            'type': 'step',
                            'condition': step['if']
                        }
                    })

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

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Actions Workflow Graph</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <style>
        body {{ font-family: sans-serif; margin: 0; padding: 0; overflow: hidden; }}
        #cy {{ width: 100vw; height: 100vh; display: block; }}
        .controls {{ position: absolute; top: 10px; left: 10px; z-index: 10; background: rgba(255,255,255,0.8); padding: 10px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.2); }}
    </style>
</head>
<body>
    <div class="controls">
        <h3>GitHub Actions Visualizer</h3>
        <ul>
            <li><p>🔵: Workflows</p></li>
            <li><p>🟢: Jobs</p></li>
            <li><p>⚫: Steps</p></li>
            <li><p>X ➔ Y: Y needs X</p></li>
        </ul>
    </div>
    <div id="cy"></div>
    <script>
        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {json.dumps(elements)},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'text-wrap': 'wrap',
                        'text-max-width': '150px',
                        'font-size': '10px'
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
                        'padding': '20px'
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
                        'padding': '10px'
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
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
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
                nodeSep: 50,
                edgeSep: 10,
                rankSep: 100
            }}
        }});
    </script>
</body>
</html>
"""
        with open(output_file, 'w') as f:
            f.write(html_template)
