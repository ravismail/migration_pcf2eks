import os
import yaml
import glob
import re
import json
import xml.etree.ElementTree as ET


def discover_app(path):
    """
    Scans the directory to identify the application type and configuration.
    Prioritizes:
    1. manifest*.yml (PCF) - checks for JBP_CONFIG_OPEN_JDK_JRE
    2. Source code heuristic (pom.xml, requirements.txt, package.json)
    """
    app_info = {
        'name': os.path.basename(os.path.abspath(path)),
        'type': None,
        'path': path,
        'env': {},
        'services': [],
        'buildpack': None,
        'java_version': None
    }

    # Search for all manifest files
    manifest_files = glob.glob(os.path.join(path, 'manifest*.yml'))
    
    # Process each manifest file
    for mf in manifest_files:
        try:
            with open(mf, 'r') as f:
                manifest = yaml.safe_load(f)
                if 'applications' in manifest and len(manifest['applications']) > 0:
                    app_data = manifest['applications'][0]
                    # Use the first app's name if we don't have one yet or if it's manifest.yml
                    if os.path.basename(mf) == 'manifest.yml' or not app_info['name']:
                        app_info['name'] = app_data.get('name', app_info['name'])
                    
                    # Merge env vars (except JBP_CONFIG_OPEN_JDK_JRE which is PCF specific)
                    app_env = app_data.get('env', {})
                    for k, v in app_env.items():
                        if k != 'JBP_CONFIG_OPEN_JDK_JRE':
                            app_info['env'][k] = v
                    
                    # services and buildpack
                    if not app_info['services']:
                        app_info['services'] = app_data.get('services', [])
                    if not app_info['buildpack']:
                        app_info['buildpack'] = app_data.get('buildpack', None)
                    
                    # Extraction of Java version from JBP_CONFIG_OPEN_JDK_JRE
                    jbp_config = app_env.get('JBP_CONFIG_OPEN_JDK_JRE', '')
                    if jbp_config:
                        # Extract version (e.g., from "{jre: {version: 17.+}}")
                        match = re.search(r'version:\s*(\d+)', str(jbp_config))
                        if match:
                            app_info['java_version'] = match.group(1)
                            app_info['type'] = 'java-maven' # Found Java config, likely Java app

                    # Heuristic from buildpack
                    if app_info['buildpack'] and not app_info['type']:
                        if 'python' in app_info['buildpack']:
                            app_info['type'] = 'python'
                        elif 'java' in app_info['buildpack']:
                            app_info['type'] = 'java-maven'
                        elif 'nodejs' in app_info['buildpack']:
                            app_info['type'] = 'nodejs'
        except Exception as e:
            print(f"Error parsing {mf}: {e}")

    # Fallback / Confirmation heuristics
    if not app_info['type']:
        if os.path.exists(os.path.join(path, 'pom.xml')):
            app_info['type'] = 'java-maven'
        elif os.path.exists(os.path.join(path, 'requirements.txt')) or os.path.exists(os.path.join(path, 'setup.py')):
            app_info['type'] = 'python'
        elif os.path.exists(os.path.join(path, 'package.json')):
            # Distinguish between Node.js and React
            try:
                with open(os.path.join(path, 'package.json'), 'r') as f:
                    package_data = json.load(f)
                    dependencies = package_data.get('dependencies', {})
                    dev_dependencies = package_data.get('devDependencies', {})
                    
                    # Detect type
                    if 'react' in dependencies or 'react' in dev_dependencies:
                        app_info['type'] = 'react'
                    else:
                        app_info['type'] = 'nodejs'
                    
                    # Extract Node version from engines field
                    engines = package_data.get('engines', {})
                    node_version = engines.get('node', '')
                    
                    if node_version:
                        # Parse version string (e.g., ">=14.0.0", "^16.0.0", "18.x")
                        # Extract major version number
                        match = re.search(r'(\d+)', node_version)
                        if match:
                            app_info['node_version'] = match.group(1)
                        else:
                            app_info['node_version'] = '18'  # Default
                    else:
                        app_info['node_version'] = '18'  # Default
                        
            except Exception as e:
                print(f"Error parsing package.json: {e}")
                app_info['type'] = 'nodejs' # Default to node if parsing fails
                app_info['node_version'] = '18'
        else:
            app_info['type'] = 'unknown'

    # Extract Java Version if Java
    if app_info['type'] == 'java-maven':
        try:
            pom_path = os.path.join(path, 'pom.xml')
            if os.path.exists(pom_path):
                tree = ET.parse(pom_path)
                root = tree.getroot()
                # Handle namespaces by ignoring them in find if possible or stripping
                ns = {'mvn': 'http://maven.apache.org/POM/4.0.0'}
                # Try with namespace
                java_ver = root.find('.//mvn:properties/mvn:java.version', ns)
                if java_ver is None:
                     # Simple scan for properties > java.version
                     for prop in root.iter():
                         if 'java.version' in prop.tag:
                             app_info['java_version'] = prop.text
                             break
                else:
                    app_info['java_version'] = java_ver.text
                
                # Extract Packaging
                packaging = root.find('.//mvn:packaging', ns)
                if packaging is None:
                    # Fallback scan
                    for elem in root.iter():
                        if 'packaging' in elem.tag:
                            app_info['packaging'] = elem.text
                            break
                else:
                     app_info['packaging'] = packaging.text
            

            if not app_info.get('java_version'):
                app_info['java_version'] = '11' # Default
            
            if not app_info.get('packaging'):
                app_info['packaging'] = 'jar' # Default

        except Exception as e:
            print(f"Error parsing java version: {e}")
            if not app_info.get('java_version'):
                app_info['java_version'] = '11'
            if not app_info.get('packaging'):
                app_info['packaging'] = 'jar'

    return app_info
