import os
import xml.etree.ElementTree as ET

def map_dependencies(path, app_type):
    """
    Maps dependencies based on application type.
    """
    dependencies = []
    
    if app_type == 'python':
        req_path = os.path.join(path, 'requirements.txt')
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dependencies.append(line)
                        
    elif app_type == 'java-maven':
        pom_path = os.path.join(path, 'pom.xml')
        if os.path.exists(pom_path):
            try:
                tree = ET.parse(pom_path)
                root = tree.getroot()
                # Handle namespaces in XML roughly or ignore them for simple parsing
                # Maven POMs usually have a namespace, making strict find difficult without registering it.
                # We'll try to find dependencies blindly or assume standard stricture.
                
                # Strip namespaces for easier parsing
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]
                        
                deps = root.find('dependencies')
                if deps is not None:
                    for dep in deps.findall('dependency'):
                        groupId = dep.find('groupId').text if dep.find('groupId') is not None else ''
                        artifactId = dep.find('artifactId').text if dep.find('artifactId') is not None else ''
                        version = dep.find('version').text if dep.find('version') is not None else ''
                        dependencies.append(f"{groupId}:{artifactId}:{version}")
            except Exception as e:
                print(f"Error parsing pom.xml: {e}")

    elif app_type in ['nodejs', 'react']:
        package_path = os.path.join(path, 'package.json')
        if os.path.exists(package_path):
            try:
                import json
                with open(package_path, 'r') as f:
                    package_data = json.load(f)
                    deps = package_data.get('dependencies', {})
                    for pkg, version in deps.items():
                        dependencies.append(f"{pkg}@{version}")
            except Exception as e:
                print(f"Error parsing package.json: {e}")
    
    return dependencies
