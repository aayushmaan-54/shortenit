import ipaddress

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Get the client IP address from the request object;
    behind a proxy, run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy ip>`
    so `request.client.host` holds the real client IP
    """
    if request.client is None:
        return "unknown"

    try:
        return str(ipaddress.ip_address(request.client.host))
    except ValueError:
        return "unknown"
