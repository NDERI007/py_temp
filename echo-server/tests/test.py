import threading
import time
import pytest
from server import EchoServer
from client import echo_client

@pytest.fixture
def echo_server():
    srv = EchoServer()
    srv.start()
    # give server a moment to start
    time.sleep(0.01)
    yield srv
    srv.stop()

def test_echo_basic(echo_server):
    resp = echo_client(echo_server.host, echo_server.port, b"hello")
    assert resp == b"hello"

def test_echo_concurrent_clients(echo_server):
    results = [None] * 5
    def worker(idx):
        results[idx] = echo_client(echo_server.host, echo_server.port, f"msg-{idx}".encode())

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=1.0)

    assert all(results[i] == f"msg-{i}".encode() for i in range(5))

def test_large_message(echo_server):
    message= b"A" * 50000
    resp = echo_client(echo_server.host, echo_server.port, message, recv_size=4096)
    assert resp == message

def test_client_disconnect(echo_server):
    import socket

    # connect and immediately close without sending
    soc = socket.create_connection((echo_server.host, echo_server.port))
    soc.close()
    time.sleep(0.05)  # give server thread a moment
    # If no exception raised, test passes

def test_timeout_behaviour(echo_server):
    import socket

    soc= socket.create_connection((echo_server.host, echo_server.port))
    soc.settimeout(0.2)
    with pytest.raises(TimeoutError):
        soc.recv(1024)

def test_empty_message(echo_server):
    message=b""
    #sending empty message should return empty
    resp = echo_client(echo_server.host, echo_server.port, message)
    assert resp == message

def test_close_mid_send(echo_server):
    import socket
    # Open socket, send part of a message, then close before finishing
    with socket.create_connection((echo_server.host, echo_server.port)) as s:
        s.sendall(b"half-message")
        # close immediately without sending rest
        # server should just echo back what it got, no crash
    time.sleep(0.05)  # give server time to handle
    # no assertion needed — test passes if server doesn’t crash