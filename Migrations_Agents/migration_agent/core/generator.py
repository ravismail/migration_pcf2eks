import os
import shutil
from jinja2 import Environment, FileSystemLoader

def generate_artifacts(app_info, output_path):
    """
    Generates Dockerfile and Helm charts using Jinja2 templates.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # Setup Jinja2 environment
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))

    # 1. Generate Dockerfile
    dockerfile_template = None
    if app_info['type'] == 'python':
        dockerfile_template = 'Dockerfile.python.j2'
    elif app_info['type'] == 'java-maven':
        dockerfile_template = 'Dockerfile.java.j2'
    elif app_info['type'] == 'nodejs':
        dockerfile_template = 'Dockerfile.nodejs.j2'
    elif app_info['type'] == 'react':
        dockerfile_template = 'Dockerfile.react.j2'
    
    if dockerfile_template:
        template = env.get_template(dockerfile_template)
        dockerfile_content = template.render(
            app_name=app_info['name'],
            env=app_info.get('env', {}),
            java_version=app_info.get('java_version', '11'),
            packaging=app_info.get('packaging', 'jar'),
            node_version=app_info.get('node_version', '18')
        )
        with open(os.path.join(output_path, 'Dockerfile'), 'w') as f:
            f.write(dockerfile_content)
        print(f"Generated Dockerfile for {app_info['type']}")
    else:
        print(f"No Dockerfile template found for type: {app_info['type']}")

    # 2. Generate Helm Chart
    chart_name = app_info['name'].lower().replace(' ', '-')
    chart_output_dir = os.path.join(output_path, 'chart', chart_name)
    if os.path.exists(chart_output_dir):
        shutil.rmtree(chart_output_dir)
    os.makedirs(chart_output_dir)

    # Render Chart.yaml and values.yaml
    for file_name in ['Chart.yaml', 'values.yaml']:
        template = env.get_template(f"chart/{file_name}.j2")
        content = template.render(app_name=chart_name)
        with open(os.path.join(chart_output_dir, file_name), 'w') as f:
            f.write(content)

    # Copy static templates
    templates_output_dir = os.path.join(chart_output_dir, 'templates')
    os.makedirs(templates_output_dir)
    
    static_templates_source = os.path.join(template_dir, 'chart', 'templates')
    for item in os.listdir(static_templates_source):
        s = os.path.join(static_templates_source, item)
        d = os.path.join(templates_output_dir, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)
            
    print(f"Generated Helm Chart: {chart_name}")
