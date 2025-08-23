import socket

def echo_client(host:str, port: int, message:bytes, recv_size:int= 4096, timeout:float= 2.0 ) -> bytes:
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(message)
        # read until we get as much as we sent (simple approach) or timeout
        received= bytearray()
        while len(received) < len(message):
            chunk= s.recv(recv_size)
            if not chunk:
                break
            received.extend(chunk) #Appends the newly received bytes into the buffer.
        return bytes(received) #when echo_client() returns, the socket is already closed by Python.(with)