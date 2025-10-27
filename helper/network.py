import json

# Store socket buffers externally (for Python 3.12 compatibility)
_socket_buffers = {}

def send_json(sock, data):
    """Send a JSON message with newline delimiter."""
    message = json.dumps(data, separators=(",", ":"), ensure_ascii=False) + "\n"
    sock.sendall(message.encode("utf-8"))

def recv_json(sock, timeout=None):
    """Receive one newline-delimited JSON object from a socket."""
    buf = _socket_buffers.get(sock.fileno(), "")
    sock.settimeout(timeout)

    try:
        while "\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                return None  # disconnected
            buf += chunk.decode("utf-8")
    except (TimeoutError, OSError):
        return None

    # Split message
    line, rest = buf.split("\n", 1)
    _socket_buffers[sock.fileno()] = rest

    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None
