# exchange information server
#!/usr/bin/env python3

import socket
import json


HOST = '0.0.0.0'
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))


while True:
    clients = []

    while True:


        data, address = server_socket.recvfrom(1024)

        # if data.decode() == 'server' or data.decode() == 'client':
        print('connection from: {}'.format(address))
        clients.append(address) 

        server_socket.sendto(b'ready', address)

        
        if len(clients) == 2:
            print('got 2 clients, sending details to each')
            break

    c1 = clients.pop()
    c1_addr, c1_port = c1
    c2 = clients.pop()
    c2_addr, c2_port = c2

    server_socket.sendto('{} {} {}'.format(c1_addr, c1_port, 5003).encode(), c2)
    server_socket.sendto('{} {} {}'.format(c2_addr, c2_port, 5003).encode(), c1)
