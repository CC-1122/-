import socket
import struct
import sys
import random

def generate_block_sizes(file_size, Lmin, Lmax, chunk_seed):
    sizes = []
    remaining = file_size
    random.seed(chunk_seed)
    
    while remaining > 0:
        if remaining <= Lmin:
            sizes.append(remaining)
            remaining = 0
        else:
            size = random.randint(Lmin, min(Lmax, remaining))
            sizes.append(size)
            remaining -= size
    
    return sizes

def main(server_ip, server_port, file_path, Lmin, Lmax, chunk_seed):
    try:
        with open(file_path, 'r', encoding='ascii') as f:
            content = f.read()
        
        file_size = len(content)
        block_sizes = generate_block_sizes(file_size, Lmin, Lmax, chunk_seed)
        n_blocks = len(block_sizes)
        
        print(f'File size: {file_size} bytes')
        print(f'Number of blocks: {n_blocks}')
        print(f'Block sizes: {block_sizes}')
        
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_ip, server_port))
        
        init_packet = struct.pack('!HI', 1, n_blocks)
        client_socket.sendall(init_packet)
        print(f'Sent Initialization: Type=1, N={n_blocks}')
        
        agree_header = client_socket.recv(2)
        if len(agree_header) >= 2:
            agree_type = struct.unpack('!H', agree_header)[0]
            print(f'Received agree: Type={agree_type}')
        else:
            print('Failed to receive agree packet')
            return
        
        reversed_parts = []
        offset = 0
        
        for i, block_size in enumerate(block_sizes, 1):
            block_data = content[offset:offset + block_size]
            offset += block_size
            
            request_packet = struct.pack('!HI', 3, block_size) + block_data.encode('ascii')
            client_socket.sendall(request_packet)
            print(f'Sent reverseRequest {i}: Length={block_size}')
            
            answer_header = client_socket.recv(6)
            if len(answer_header) >= 6:
                answer_type, data_len = struct.unpack('!HI', answer_header)
                
                reversed_data = b''
                while len(reversed_data) < data_len:
                    chunk = client_socket.recv(data_len - len(reversed_data))
                    if not chunk:
                        break
                    reversed_data += chunk
                
                if len(reversed_data) == data_len:
                    reversed_str = reversed_data.decode('ascii')
                    reversed_parts.append(reversed_str)
                    print(f'{i}: {reversed_str}')
                else:
                    print(f'Incomplete reverseAnswer for block {i}')
                    break
            else:
                print(f'Failed to receive reverseAnswer for block {i}')
                break
        
        client_socket.close()
        
        full_reversed = ''.join(reversed_parts)
        output_file = 'reversed_' + file_path
        with open(output_file, 'w', encoding='ascii') as f:
            f.write(full_reversed)
        
        print(f'\nFull reversed text written to {output_file}')
        print(f'Total reversed characters: {len(full_reversed)}')
        
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) != 7:
        print('Usage: python reversetcpclient.py <server_ip> <server_port> <file_path> <Lmin> <Lmax> <chunk_seed>')
        print('Example: python reversetcpclient.py 127.0.0.1 8888 test.txt 50 100 42')
        sys.exit(1)
    
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    file_path = sys.argv[3]
    Lmin = int(sys.argv[4])
    Lmax = int(sys.argv[5])
    chunk_seed = int(sys.argv[6])
    
    main(server_ip, server_port, file_path, Lmin, Lmax, chunk_seed)
