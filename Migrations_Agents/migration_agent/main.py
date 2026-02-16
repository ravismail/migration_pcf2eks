import click
from migration_agent.core.discovery import discover_app
from migration_agent.core.dependency import map_dependencies
from migration_agent.core.generator import generate_artifacts

@click.command()
@click.option('--source', prompt='Source directory', help='Path to the application source code.')
@click.option('--output', default='./output', help='Path to save generated artifacts.')
def migrate(source, output):
    """Platform Migration Agent: PCF -> Kubernetes"""
    click.echo(f"Starting migration for: {source}")
    
    app_info = discover_app(source)
    if not app_info:
        click.echo("Could not determine application type.")
        return

    click.echo(f"Detected application: {app_info}")
    
    dependencies = map_dependencies(source, app_info['type'])
    click.echo(f"Dependencies: {len(dependencies)} found.")
    
    generate_artifacts(app_info, output)
    click.echo(f"Artifacts generated in: {output}")

if __name__ == '__main__':
    migrate()
