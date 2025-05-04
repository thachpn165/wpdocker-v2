import pytest
from unittest.mock import patch, MagicMock
from src.features.mysql.database import create_database

@pytest.fixture
def mock_env():
    return {"MYSQL_CONTAINER_NAME": "test_mysql_container"}

@pytest.fixture
def mock_mysql_client():
    return "mysql"

@pytest.fixture
def mock_get_mysql_root_password():
    with patch("src.features.mysql.database.get_mysql_root_password") as mock:
        yield mock

@pytest.fixture
def mock_subprocess_run():
    with patch("src.features.mysql.database.subprocess.run") as mock:
        yield mock

@pytest.fixture
def mock_error():
    with patch("src.features.mysql.database.error") as mock:
        yield mock

@pytest.fixture
def mock_info():
    with patch("src.features.mysql.database.info") as mock:
        yield mock

def test_create_database_success(
    mock_env, mock_mysql_client, mock_get_mysql_root_password, mock_subprocess_run, mock_info
):
    # Arrange
    domain = "example.com"
    db_name = "example_com_wpdb"
    mock_get_mysql_root_password.return_value = "root_password"
    mock_subprocess_run.return_value = MagicMock()

    with patch("src.features.mysql.database.env", mock_env), \
         patch("src.features.mysql.database.mysql_client", mock_mysql_client):
        # Act
        result = create_database(domain)

    # Assert
    assert result == db_name
    mock_get_mysql_root_password.assert_called_once()
    mock_subprocess_run.assert_called_once_with(
        [
            "docker", "exec", "-i", mock_env["MYSQL_CONTAINER_NAME"],
            mock_mysql_client, "-uroot", "-proot_password",
            "-e", f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        ],
        check=True
    )
    mock_info.assert_called_once_with(f"✅ Đã tạo database: {db_name}")

def test_create_database_no_root_password(
    mock_env, mock_mysql_client, mock_get_mysql_root_password, mock_error
):
    # Arrange
    domain = "example.com"
    mock_get_mysql_root_password.return_value = None

    with patch("src.features.mysql.database.env", mock_env), \
         patch("src.features.mysql.database.mysql_client", mock_mysql_client):
        # Act
        result = create_database(domain)

    # Assert
    assert result is None
    mock_get_mysql_root_password.assert_called_once()
    mock_error.assert_called_once_with("❌ Không lấy được mật khẩu root MySQL.")

def test_create_database_subprocess_error(
    mock_env, mock_mysql_client, mock_get_mysql_root_password, mock_subprocess_run, mock_error
):
    # Arrange
    domain = "example.com"
    db_name = "example_com_wpdb"
    mock_get_mysql_root_password.return_value = "root_password"
    mock_subprocess_run.side_effect = Exception("Subprocess error")

    with patch("src.features.mysql.database.env", mock_env), \
         patch("src.features.mysql.database.mysql_client", mock_mysql_client):
        # Act
        result = create_database(domain)

    # Assert
    assert result is None
    mock_get_mysql_root_password.assert_called_once()
    mock_subprocess_run.assert_called_once_with(
        [
            "docker", "exec", "-i", mock_env["MYSQL_CONTAINER_NAME"],
            mock_mysql_client, "-uroot", "-proot_password",
            "-e", f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        ],
        check=True
    )
    mock_error.assert_called_once_with("❌ Lỗi khi tạo database: Subprocess error")