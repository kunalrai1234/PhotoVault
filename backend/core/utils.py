import os
import sys
import socket

def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for development and PyInstaller bundled builds.
    """
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # Development mode: root directory is two levels above backend/core
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return os.path.normpath(os.path.join(base_path, relative_path))

def find_available_port(start_port: int = 54321, max_attempts: int = 20) -> int:
    """
    Finds an available local port starting from start_port.
    Avoids collisions with running instances or other applications.
    """
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start_port

