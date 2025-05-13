"""
Path mapping for migration from old structure to new structure.

This module provides constants and utilities for mapping paths between
the old directory structure and the new refactored structure.
"""

from typing import Dict, Tuple


# Path mappings from old to new structure
OLD_TO_NEW_PATHS: Dict[str, str] = {
    # Core environment
    "core/core.env": "src/config/core.env",
    
    # Templates
    "core/templates/docker-compose.mysql.yml.template": "src/templates/docker-compose/docker-compose.mysql.yml.template",
    "core/templates/docker-compose.nginx.yml.template": "src/templates/docker-compose/docker-compose.nginx.yml.template",
    "core/templates/docker-compose.php.yml.template": "src/templates/docker-compose/docker-compose.php.yml.template",
    "core/templates/docker-compose.rclone.yml.template": "src/templates/docker-compose/docker-compose.rclone.yml.template",
    "core/templates/docker-compose.redis.yml.template": "src/templates/docker-compose/docker-compose.redis.yml.template",
    "core/templates/docker-compose.wpcli.yml.template": "src/templates/docker-compose/docker-compose.wpcli.yml.template",
    "core/templates/nginx-domain.conf.template": "src/templates/nginx/nginx-domain.conf.template",
    "core/templates/nginx-vhost.conf.template": "src/templates/nginx/nginx-vhost.conf.template",
    "core/templates/nginx.conf.template": "src/templates/nginx/nginx.conf.template", 
    "core/templates/php.ini.template": "src/templates/php/php.ini.template",
    "core/templates/wpcli-custom.ini": "src/templates/wpcli/wpcli-custom.ini",
    
    # Bash utils
    "core/bash-utils/file_operations.sh": "src/bash/file_operations.sh",
    "core/bash-utils/get_path.sh": "src/bash/get_path.sh",
    "core/bash-utils/load_config.sh": "src/bash/load_config.sh",
    "core/bash-utils/messages_utils.sh": "src/bash/messages_utils.sh",
    "core/bash-utils/validate.sh": "src/bash/validate.sh",
    
    # WordPress
    "core/wp/wp-cli.phar": "src/wordpress/wp-cli.phar",
    
    # Core modules -> src/core
    "core/backend/objects/config.py": "src/core/config/manager.py",
    "core/backend/objects/container.py": "src/core/containers/container.py",
    "core/backend/objects/compose.py": "src/core/containers/compose.py",
    "core/backend/objects/downloader.py": "src/core/utils/downloader.py",
    "core/backend/objects/menu.py": "src/core/ui/menu.py",
    "core/backend/models/config.py": "src/core/models/site_config.py",
    
    # Bootstrap modules
    "core/backend/bootstraps/config_bootstrap.py": "src/core/bootstrap/config.py",
    "core/backend/bootstraps/system_bootstrap.py": "src/core/bootstrap/system.py",
    "core/backend/bootstraps/docker_bootstrap.py": "src/core/bootstrap/docker.py",
    "core/backend/bootstraps/mysql_bootstrap.py": "src/core/bootstrap/mysql.py",
    "core/backend/bootstraps/nginx_bootstrap.py": "src/core/bootstrap/nginx.py",
    "core/backend/bootstraps/redis_bootstrap.py": "src/core/bootstrap/redis.py",
    "core/backend/bootstraps/webserver_bootstrap.py": "src/core/bootstrap/webserver.py",
    "core/backend/bootstraps/wpcli_bootstrap.py": "src/core/bootstrap/wpcli.py",
    "core/backend/bootstraps/rclone_bootstrap.py": "src/core/bootstrap/rclone.py",
    "core/backend/bootstraps/misc_bootstrap.py": "src/core/bootstrap/misc.py",
    
    # Loader and initializer
    "core/backend/core_loader.py": "src/core/loader.py",
    "core/backend/init.py": "src/core/init.py",
    
    # Common utilities
    "core/backend/utils/container_utils.py": "src/common/utils/container.py",
    "core/backend/utils/crypto.py": "src/common/utils/crypto.py",
    "core/backend/utils/debug.py": "src/common/logging.py",
    "core/backend/utils/editor.py": "src/common/utils/editor.py",
    "core/backend/utils/env_utils.py": "src/common/utils/environment.py",
    "core/backend/utils/password.py": "src/common/utils/password.py",
    "core/backend/utils/system_info.py": "src/common/utils/system_info.py",
    "core/backend/utils/validate.py": "src/common/utils/validation.py",
    "core/backend/utils/webserver_utils.py": "src/common/webserver/utils.py",
    
    # Abstract classes
    "core/backend/abc/php_extension.py": "src/interfaces/AbstractPHPExtension.py",
    "core/backend/abc/prompt_base.py": "src/interfaces/AbstractPrompt.py",
}

# Import patterns that need to be updated
IMPORT_PATTERNS: Dict[str, str] = {
    "from core.backend.utils.debug import": "from src.common.logging import",
    "from core.backend.utils.env_utils import": "from src.common.utils.environment import",
    "from core.backend.utils.crypto import": "from src.common.utils.crypto import",
    "from core.backend.utils.validate import": "from src.common.utils.validation import",
    "from core.backend.utils.password import": "from src.common.utils.password import",
    "from core.backend.utils.system_info import": "from src.common.utils.system_info import",
    "from core.backend.utils.editor import": "from src.common.utils.editor import",
    "from core.backend.utils.container_utils import": "from src.common.utils.container import",
    "from core.backend.utils.webserver_utils import": "from src.common.webserver.utils import",
    
    "from core.backend.objects.config import": "from src.common.config.manager import",
    "from core.backend.objects.container import": "from src.core.containers.container import",
    "from core.backend.objects.compose import": "from src.core.containers.compose import",
    "from core.backend.objects.downloader import": "from src.core.utils.downloader import",
    "from core.backend.objects.menu import": "from src.core.ui.menu import",
    
    "from core.backend.models.config import": "from src.core.models import",
    
    "from core.backend.abc.php_extension import": "from src.interfaces.AbstractPHPExtension import",
    "from core.backend.abc.prompt_base import": "from src.interfaces.AbstractPrompt import",
    
    # Module imports
    "from core.backend.modules.": "from src.features.",
}

# Environment variable name changes (if any)
ENV_VAR_CHANGES: Dict[str, str] = {
    "TEMPLATE_DIR": "src/templates",
    "CONFIG_DIR": "src/config",
    "BASH_UTILS_DIR": "src/bash",
    "WP_CLI_DIR": "src/wordpress",
}

def get_new_path(old_path: str) -> str:
    """
    Get the new path for a given old path.
    
    Args:
        old_path: Path in the old structure
        
    Returns:
        Corresponding path in the new structure or the original if not found
    """
    return OLD_TO_NEW_PATHS.get(old_path, old_path)

def update_import_statement(import_line: str) -> str:
    """
    Update an import statement from old structure to new structure.
    
    Args:
        import_line: Original import statement
        
    Returns:
        Updated import statement
    """
    for old_pattern, new_pattern in IMPORT_PATTERNS.items():
        if import_line.startswith(old_pattern):
            # Replace the import pattern
            return import_line.replace(old_pattern, new_pattern)
            
    return import_line