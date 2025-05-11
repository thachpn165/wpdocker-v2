"""
CLI interface for changing system language.

This module provides a command-line interface for changing the system language,
handling user input validation and parameter collection.
"""

import sys
from typing import Optional, List
import click
import questionary
from src.features.system.manager import SystemManager
from src.common.logging import debug, info, error, success, log_call

# List of supported languages
LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "vi", "name": "Tiếng Việt"},
]


def get_language_choices() -> List[dict]:
    """
    Get language choices for prompt selection.

    Returns:
        List[dict]: List of language choices with name and value
    """
    return [
        {"name": f"{lang['name']} ({lang['code']})", "value": lang['code']}
        for lang in LANGUAGES
    ]


@log_call
def cli_change_language(lang_code: Optional[str] = None, interactive: bool = True) -> bool:
    """
    Implementation of the change language command.

    Args:
        lang_code: Language code to set (en/vi)
        interactive: Whether this is run in interactive mode (True for menu, False for CLI)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        debug(f"Executing change_language with lang_code={lang_code}, interactive={interactive}")
        manager = SystemManager()

        # If language code not provided and in interactive mode, prompt for selection
        if lang_code is None and interactive:
            lang_choice = questionary.select(
                "Chọn ngôn ngữ:",
                choices=get_language_choices()
            ).ask()

            if lang_choice is None:  # User cancelled
                if interactive:
                    info("Đã hủy thay đổi ngôn ngữ.")
                return False

            lang_code = lang_choice

        # If no language was selected or provided
        if lang_code is None:
            if interactive:
                error("Không có ngôn ngữ nào được chọn.")
            return False

        # Validate the language code
        valid_codes = [l["code"] for l in LANGUAGES]
        if lang_code not in valid_codes:
            if interactive:
                error(f"Ngôn ngữ không hợp lệ: {lang_code}. Các mã hợp lệ: {', '.join(valid_codes)}")
            return False

        # Set the language
        manager.set_language(lang_code)

        # Get the full language name for display
        lang_name = next(l['name'] for l in LANGUAGES if l['code'] == lang_code)

        if interactive:
            success(f"Đã chuyển sang ngôn ngữ: {lang_name}")

        return True
    except Exception as e:
        error(f"Lỗi khi thay đổi ngôn ngữ: {str(e)}")
        return False


@click.command(name="change-language")
@click.option('--lang', 'lang_code', help='Language code to set (en/vi)')
def change_language_cli(lang_code: Optional[str] = None) -> None:
    """Change the system language."""
    result = cli_change_language(lang_code, interactive=False)
    if not result:
        ctx = click.get_current_context()
        ctx.exit(1)


if __name__ == "__main__":
    sys.exit(0 if cli_change_language() else 1)
