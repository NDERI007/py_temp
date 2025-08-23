import socket
import threading
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO) #Configures the logger to show messages at INFO level and above.
logger = logging.getLogger(__name__) #Configures the logger to show messages at INFO level and above.

class EchoServer:
    def __init__(self, host: str="127.0.0.1", port: int = 0, backlog: int = 5):
        self._host = host
        self._port = port
        self._backlog = backlog
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._host, self._port) #tell the OS “I’ll accept connections for this address and port”.
        self._host, self._port = self._sock.getsockname() # returns the actual address/port bound. Important when port=0 so you can discover which port the OS picked.
        self._sock.listen(self._backlog) #mark this socket as a listening socket (ready to accept connections).The backlog value controls the size of this completed connection queue.
        self._running = threading.Event() # a thread-safe flag (on/off) that lets threads check whether server should keep running. You call .set() or .clear() to change it.
        self._accept_thread = None #will hold the background thread that accepts incoming connections.
        self._handler_threads : List[threading.Thread] = [] #list to track per-client handler threads so we can join (wait for) them when stopping.

    def start(self):
        self._running.set()
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()
        logger.info("EchoServer started on %s:%d", self._host, self._port)

    def _accept_loop(self):
        try:
            while self._running.is_set(): # ✅ check flag, don't overwrite
                try:
                    client_sock, addr = self._sock.accept()
                except OSError:
                 #SOCKET CLOSED
                 break
                t = threading.Thread(target=self._handleClient, args=(client_sock,), daemon=True)
                t.start()
                self._handler_threads.append(t)
        finally: # This will only run when your _accept_loop exits (e.g. when you stop the server or it crashes)
            try:
             self._sock.close()
            except Exception:
               pass
    
    def handleClient(self, client_sock: socket.socket):
       with client_sock:
          client_sock.settimeout(1.0)
          while True:
            try:
               data = client_sock.recv(4096) #If the client sent more than 4096 bytes, you’ll only get the first chunk.
               #The rest stays in the socket buffer, waiting for you to call .recv() again.
               #So you’d typically loop and keep calling .recv() until you’ve read everything.
            except socket.timeout:
               #If no data arrives within 1 second, just loop and try again.
               continue
            except OSError:
               break
            if not data:
               break
            try:
               client_sock.sendall(data)
            except OSError:
               break
        # ← only when you exit this block, client_sock.close() is called

    def stop(self):
       self._running.clear()
       try:
          # this helps release a blocking accept()
          self._sock.shutdown(socket.SHUT_RDWR)
       except Exception:
        pass
       try:
          self._sock.close()
       except Exception:
        pass
       
       if self._accept_thread:
          self._accept_thread.join(timeout=1.0)
       for t in self._handler_threads:
          t.join(timeout=0.1)
       logger.info("EchoServer stopped")
       