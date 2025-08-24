import asyncio

async def handle_echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while True:
            try:
             data = await asyncio.wait_for(reader.read(4096), timeout=30.0)
            except asyncio.TimeoutError:
             print("Inactivity timeout") 
             break  # disconnect idle client
            if not data:
                break
            writer.write(data)
            await writer.drain() #waits until the buffer is sufficiently empty (flushed into the OS).
    finally:
        writer.close()
        await writer.wait_closed() #is the async equivalent of thread.join() for sockets

async def run_server(host="127.0.0.1", port=0):
    server = await asyncio.start_server(handle_echo, host, port) #Binding = locking the socket to a network address so clients know where to connect.
    sockets = server.sockets
    if not sockets: #it makes sure the server really did create at least one listening socket.
        raise RuntimeError("No sockets bound")
    addr = sockets[0].getsockname()
    return server, addr  # caller can `await server.serve_forever()` or use context manager

#Transport buffer = staging area in Python before handing to the OS.

#OS flushing = moving staged data into the kernel socket buffer, then onto the network.