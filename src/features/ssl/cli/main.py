"""
SSL certificate management CLI.

This module provides the command-line interface for SSL certificate management.
"""

import argparse
from typing import Optional

from src.common.logging import log_call, debug, error, info, warn, success
from src.features.ssl.core.installer import (
    install_selfsigned_ssl,
    install_manual_ssl,
    install_letsencrypt_ssl
)
from src.features.ssl.core.checker import check_ssl, get_ssl_status
from src.features.ssl.core.editor import edit_ssl, read_ssl_files


def create_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for SSL management.
    
    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="SSL certificate management",
        epilog="""
Examples:
  # Install self-signed certificate
  wpdocker ssl install selfsigned example.com
  
  # Install Let's Encrypt certificate
  wpdocker ssl install letsencrypt example.com --email admin@example.com
  
  # Check certificate status
  wpdocker ssl check example.com
  
  # Edit certificate configuration
  wpdocker ssl edit example.com --cert /path/to/cert.pem --key /path/to/key.pem
"""
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install SSL certificate")
    install_parser.add_argument("type", choices=["selfsigned", "manual", "letsencrypt"],
                              help="Certificate type")
    install_parser.add_argument("domain", help="Domain name")
    install_parser.add_argument("--email", help="Email address")
    install_parser.add_argument("--cert", help="Path to certificate file (for manual)")
    install_parser.add_argument("--key", help="Path to private key file (for manual)")
    install_parser.add_argument("--chain", help="Path to certificate chain file (for manual)")
    install_parser.add_argument("--no-auto-renew", action="store_true",
                              help="Disable auto-renewal (for Let's Encrypt)")
                              
    # Check command
    check_parser = subparsers.add_parser("check", help="Check SSL certificate")
    check_parser.add_argument("domain", help="Domain name")
    
    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit SSL configuration")
    edit_parser.add_argument("domain", help="Domain name")
    edit_parser.add_argument("--cert", help="Path to new certificate file")
    edit_parser.add_argument("--key", help="Path to new private key file")
    edit_parser.add_argument("--chain", help="Path to new certificate chain file")
    edit_parser.add_argument("--email", help="Email address for notifications")
    edit_parser.add_argument("--auto-renew", action="store_true",
                           help="Enable auto-renewal")
    edit_parser.add_argument("--no-auto-renew", action="store_true",
                           help="Disable auto-renewal")
                           
    return parser


@log_call
def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main entry point for SSL management CLI.
    
    Args:
        args: Command-line arguments
        
    Returns:
        int: Exit code
    """
    parser = create_parser()
    args = args or parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
        
    try:
        if args.command == "install":
            if args.type == "selfsigned":
                success = install_selfsigned_ssl(args.domain, args.email)
            elif args.type == "manual":
                if not args.cert or not args.key:
                    error("Certificate and key files are required for manual installation")
                    return 1
                success = install_manual_ssl(args.domain, args.cert, args.key, args.chain)
            else:  # letsencrypt
                if not args.email:
                    error("Email address is required for Let's Encrypt")
                    return 1
                success = install_letsencrypt_ssl(args.domain, args.email, not args.no_auto_renew)
                
            return 0 if success else 1
            
        elif args.command == "check":
            status = get_ssl_status(args.domain)
            print(status)
            return 0
            
        elif args.command == "edit":
            auto_renew = None
            if args.auto_renew:
                auto_renew = True
            elif args.no_auto_renew:
                auto_renew = False
                
            success = edit_ssl(
                args.domain,
                args.cert,
                args.key,
                args.chain,
                auto_renew,
                args.email
            )
            return 0 if success else 1
            
        else:
            parser.print_help()
            return 1
            
    except Exception as e:
        error(f"Error executing command: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())