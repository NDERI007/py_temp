import asyncio
import pytest
from async_echo import run_server

@pytest.mark.asyncio
async def test_echo_Server():
    server, addr = await run_server()
    host, port = addr

    async with server: #ensures cleanup
        reader, writer = await asyncio.open_connection(host, port)

        message=b"yooooh twin"
        writer.write(message)
        await writer.drain()

        #receive echo
        data= await reader.read(len(message))
        assert data == message

        #close client
        writer.close()
        await writer.wait_closed()

@pytest.mark.asyncio
async def test_empty_message():
    server, addr = await run_server()
    host, port = addr

    async with server:
        reader, writer = await asyncio.open_connection(host, port)

        writer.close()
        await writer.wait_closed()

        # give server a short moment to process closure
        await asyncio.sleep(0.1)

        # if server crashed, test will fail; otherwise it passes
        assert server.sockets  # still running

@pytest.mark.asyncio
async def test_inactivity_timeout():
    server, addr = await run_server()
    host, port = addr

    async with server:
        reader, writer = await asyncio.open_connection(host, port)

        # don’t send anything, just wait longer than timeout
        with pytest.raises(asyncio.IncompleteReadError):
            # server should eventually close connection
            await reader.readexactly(1)

        writer.close()
        await writer.wait_closed()

@pytest.mark.asyncio
async def test_multiple_clients_concurrently():
    server, addr = await run_server()
    host, port = addr

    async with server:
        async def client_task(msg: bytes):
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(msg)
            await writer.drain()
            data = await reader.read(len(msg))
            writer.close()
            await writer.wait_closed()
            return data

        msgs = [b"hello", b"world", b"asyncio", b"rocks"]
        results = await asyncio.gather(*(client_task(m) for m in msgs))

        assert results == msgs  # echo matches input
