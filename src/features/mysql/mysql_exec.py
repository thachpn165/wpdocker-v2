"""
MySQL command execution functions.

This module provides functions for executing MySQL commands in a container,
including queries, imports, and dumps.
"""

from typing import Optional, Dict, List, Any

from src.common.utils.environment import env_required, env
from src.common.containers.container import Container
from src.features.mysql.utils import detect_mysql_client, get_mysql_root_password


# Ensure required environment variables are set
env_required(["MYSQL_CONTAINER_NAME"])
mysql_container = Container(env["MYSQL_CONTAINER_NAME"])


def run_mysql_command(query: str, db: Optional[str] = None) -> str:
    """
    Execute a MySQL command in the container.
    
    Args:
        query: SQL query to execute
        db: Optional database name
        
    Returns:
        Command output
    """
    container = mysql_container
    client = detect_mysql_client(container)
    pwd = get_mysql_root_password()
    db_part = f"{db}" if db else ""
    cmd = f"{client} -u root {db_part} -e \"{query}\""
    return container.exec(["sh", "-c", cmd], user="root", envs={"MYSQL_PWD": pwd})


def run_mysql_import(sql_path: str, db: str) -> str:
    """
    Import SQL file into database in the container.
    
    Args:
        sql_path: Path to the SQL file in the container
        db: Database name
        
    Returns:
        Command output
    """
    container = mysql_container
    client = detect_mysql_client(container)
    pwd = get_mysql_root_password()
    cmd = f"{client} -u root {db} < {sql_path}"
    return container.exec(["sh", "-c", cmd], user="root", envs={"MYSQL_PWD": pwd})


def run_mysql_dump(db: str, output_path_in_container: str) -> str:
    """
    Dump database to SQL file in the container.
    
    Args:
        db: Database name
        output_path_in_container: Path where to save the SQL file in the container
        
    Returns:
        Command output
    """
    container = mysql_container
    client = detect_mysql_client(container)
    pwd = get_mysql_root_password()
    dump_cmd = "mariadb-dump" if client == "mariadb" else "mysqldump"
    cmd = f"{dump_cmd} -u root {db} > {output_path_in_container}"
    return container.exec(["sh", "-c", cmd], user="root", envs={"MYSQL_PWD": pwd})