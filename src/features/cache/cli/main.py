import click
from src.features.cache.core.setup import setup_fastcgi_cache
from src.common.logging import info, error

@click.group()
def cache_cli():
    """Cache management commands."""
    pass

@cache_cli.command("setup-fastcgi")
@click.option('--domain', prompt=True, help='Domain name of the website')
def cli_setup_fastcgi_cache(domain):
    """Set up fastcgi-cache for a WordPress site and configure NGINX."""
    if setup_fastcgi_cache(domain):
        info(f"FastCGI cache setup completed for {domain}")
    else:
        error(f"Failed to set up FastCGI cache for {domain}") 