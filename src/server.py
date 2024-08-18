from typing import Tuple
import subprocess
from dnslib import DNSRecord, DNSQuestion, DNSLabel
import socket


class DnsServer:

    def __init__(self):  
        self.handlers = {}

    def query(self, qtype):
        def decorator(callback):
            print('Updating handler for qtype:', qtype)
            self.handlers[qtype] = callback
            return callback
        return decorator

    def handle_request(
        self,
        data: bytes,
        addr: Tuple[str, int],
        server_socket: socket.socket
    ):
        request = DNSRecord.parse(data)
        response = request.reply()

        for question in request.questions:
            if not isinstance(question, DNSQuestion):
                raise TypeError

            handler = self.handlers.get(question.qtype)
            if handler is None:
                response.header.rcode = 4
                continue

            handler(question.qname, response)

        server_socket.sendto(response.pack(), addr)

    def run(self, port, host='127.0.0.1'):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((host, port))
        
        try:
            subprocess.run(['sudo', 'resolvectl', 'flush-caches'], check=True)
            print("DNS cache cleared.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to clear DNS cache: {e}")

        try:
            while True:
                data, addr = server_socket.recvfrom(512)
                self.handle_request(data, addr, server_socket)
        except KeyboardInterrupt:
            print("Servidor DNS interrompido.")
            server_socket.close()

