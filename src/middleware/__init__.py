from fastmcp import FastMCP

from .auth_middleware import AuthMiddleware


def register_middleware(server: FastMCP):
    server.add_middleware(AuthMiddleware())
