#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CCAE Cross-Cultural Adaptation Engine — Entry Point

Usage:
    python run.py                       # start with defaults (0.0.0.0:5000, debug)
    python run.py --port 8080           # custom port
    python run.py --host 127.0.0.1       # local only
    python run.py --no-debug            # production mode

GitHub: https://github.com/2187262974-cmd/ccae-engine
"""

import argparse
import os
import sys
import io

# 修复Windows终端中文输出乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Ensure backend/ is on the Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)


def parse_args():
    parser = argparse.ArgumentParser(
        description="CCAE Cross-Cultural Adaptation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python run.py                          # start on http://0.0.0.0:5000
  python run.py --port 8080 --host 127.0.0.1
  python run.py --no-debug
        """,
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="bind address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="bind port (default: 5000)"
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="disable Flask debug mode (use in production)",
    )
    return parser.parse_args()


def main():
    from dotenv import load_dotenv
    load_dotenv()

    args = parse_args()

    # Late import: let sys.path resolve backend modules
    from app import app, init_db, seed_initial_data

    init_db()
    seed_initial_data()

    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1", "yes")
    if not args.no_debug:
        debug = True
    print("=" * 50)
    print("  CCAE Cross-Cultural Adaptation Engine")
    print("=" * 50)
    print(f"  Management UI : http://{args.host}:{args.port}/")
    print(f"  API Base      : http://{args.host}:{args.port}/api")
    print(f"  Debug Mode    : {'ON' if debug else 'OFF'}")
    print("=" * 50)
    print()

    app.run(debug=debug, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
