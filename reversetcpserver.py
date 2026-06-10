import socket
import threading
import struct
import time
import os

LOG_FILE = 'run_log.txt'

def log_message(msg):
    now = time.localtime()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', now)
    ms = int(time.time() * 1000) % 1000
    timestamp = f'{timestamp}.{ms:03d}'
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {msg}\n')

def reverse_text(data):
    return data[::-1]

def handle_client(client_socket, client_addr):
    log_message(f'New client connected: {client_addr}')
    
    try:
        header = client_socket.recv(6)
        if len(header) < 6:
            log_message(f'Client {client_addr} disconnected (no header)')
            return
        
        type_field, n_blocks = struct.unpack('!HI', header)
        log_message(f'Received Initialization from {client_addr}: Type={type_field}, N={n_blocks}')
        
        agree_packet = struct.pack('!H', 2)
        client_socket.sendall(agree_packet)
        log_message(f'Sent agree to {client_addr}')
        
        for block_num in range(1, n_blocks + 1):
            header = client_socket.recv(6)
            if len(header) < 6:
                log_message(f'Client {client_addr} disconnected during transfer')
                break
            
            type_field, length = struct.unpack('!HI', header)
            log_message(f'Received reverseRequest from {client_addr}: Type={type_field}, Length={length}')
            
            data = b''
            while len(data) < length:
                chunk = client_socket.recv(length - len(data))
                if not chunk:
                    break
                data += chunk
            
            if len(data) == length:
                reversed_data = reverse_text(data.decode('ascii')).encode('ascii')
                reversed_len = len(reversed_data)
                
                answer_packet = struct.pack('!HI', 4, reversed_len) + reversed_data
                client_socket.sendall(answer_packet)
                log_message(f'Sent reverseAnswer to {client_addr}: Length={reversed_len}')
            else:
                log_message(f'Incomplete data from {client_addr}, expected {length}, got {len(data)}')
                break
        
    except Exception as e:
        log_message(f'Error handling client {client_addr}: {str(e)}')
    finally:
        client_socket.close()
        log_message(f'Client {client_addr} disconnected')

def main(port=8888):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    log_message(f'Server started on port {port}')
    print(f'Server listening on port {port}...')
    
    try:
        while True:
            client_socket, client_addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_addr))
            client_thread.start()
    except KeyboardInterrupt:
        log_message('Server shutting down')
        print('Server shutting down...')
    finally:
        server_socket.close()

if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    main(port)
