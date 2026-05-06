import yaml
import os
import glob

class WorkflowParser:
    def __init__(self, directory):
        self.directory = directory
        self.workflows = []

    def parse(self):
        files = glob.glob(os.path.join(self.directory, "*.yml")) + glob.glob(os.path.join(self.directory, "*.yaml"))
        for file_path in files:
            with open(file_path, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    if not data or 'jobs' not in data:
                        continue
                    
                    workflow_info = {
                        'filename': os.path.basename(file_path),
                        'name': data.get('name', os.path.basename(file_path)),
                        'on': data.get('on', {}),
                        'jobs': []
                    }

                    for job_id, job_data in data.get('jobs', {}).items():
                        job_info = {
                            'id': job_id,
                            'name': job_data.get('name', job_id),
                            'needs': job_data.get('needs', []),
                            'if': job_data.get('if', None),
                            'uses': job_data.get('uses', None),
                            'steps': []
                        }
                        
                        # Normalize needs to a list
                        if isinstance(job_info['needs'], str):
                            job_info['needs'] = [job_info['needs']]

                        for step in job_data.get('steps', []):
                            step_info = {
                                'name': step.get('name', step.get('uses', step.get('run', 'Unnamed Step'))),
                                'if': step.get('if', None),
                                'uses': step.get('uses', None)
                            }
                            job_info['steps'].append(step_info)
                        
                        workflow_info['jobs'].append(job_info)
                    
                    self.workflows.append(workflow_info)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
        
        return self.workflows

if __name__ == "__main__":
    import json
    parser = WorkflowParser("examples")
    print(json.dumps(parser.parse(), indent=2))
