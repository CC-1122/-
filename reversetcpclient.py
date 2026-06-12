# TCP Socket 客户端程序
# 功能：读取ASCII文件，分块发送给服务器进行反转，接收结果并保存

# 导入需要的模块
import socket       # 用于网络通信
import struct       # 用于数据打包/解包（网络字节序）
import sys          # 用于命令行参数
import random       # 用于生成随机分块大小

def generate_block_sizes(file_size, Lmin, Lmax, chunk_seed):
    """
    生成数据块大小列表（核心分块算法）
    :param file_size: 文件总大小（字节）
    :param Lmin: 最小块大小
    :param Lmax: 最大块大小
    :param chunk_seed: 随机数种子（保证结果可重现）//方便重现分块结果，定位bug
    :return: 分块大小列表
    """
    sizes = []           # 存储每个块的大小
    remaining = file_size  # 剩余未分块的字节数
    random.seed(chunk_seed)  # 设置随机种子，保证分块结果可重现
    
    # 循环分块直到所有数据都被分配
    while remaining > 0:
        # 如果剩余字节数小于等于最小块大小，全部作为最后一块
        if remaining <= Lmin:
            sizes.append(remaining)
            remaining = 0
        else:
            # 在 [Lmin, min(Lmax, remaining)] 范围内随机生成块大小
            # min(Lmax, remaining) 确保不会超过剩余字节数
            size = random.randint(Lmin, min(Lmax, remaining))
            sizes.append(size)
            remaining -= size  # 更新剩余字节数
    
    return sizes  # 返回分块大小列表

def main(server_ip, server_port, file_path, Lmin, Lmax, chunk_seed):
    """
    客户端主函数
    :param server_ip: 服务器IP地址
    :param server_port: 服务器端口
    :param file_path: 要反转的文件路径
    :param Lmin: 最小分块大小
    :param Lmax: 最大分块大小
    :param chunk_seed: 随机分块种子
    """
    try:
        # ========== 阶段1：读取文件内容 ==========
        # 以ASCII编码读取文件内容
        with open(file_path, 'r', encoding='ascii') as f:
            content = f.read()
        
        # 获取文件大小并生成分块
        file_size = len(content)
        block_sizes = generate_block_sizes(file_size, Lmin, Lmax, chunk_seed)
        n_blocks = len(block_sizes)  # 数据块总数
        
        # 输出分块信息（调试用）
        print(f'File size: {file_size} bytes')
        print(f'Number of blocks: {n_blocks}')
        print(f'Block sizes: {block_sizes}')
        
        # ========== 阶段2：建立TCP连接 ==========
        # 创建TCP套接字
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 连接到服务器
        client_socket.connect((server_ip, server_port))
        
        # ========== 阶段3：发送初始化报文 ==========
        # 构造 Initialization 报文（Type=1，N=块数）
        # '!HI' = 网络字节序 + 无符号短整型(2字节) + 无符号整型(4字节)
        init_packet = struct.pack('!HI', 1, n_blocks)
        client_socket.sendall(init_packet)  # 发送初始化请求
        print(f'Sent Initialization: Type=1, N={n_blocks}')
        
        # 接收服务器的确认报文（Agree，Type=2）
        agree_header = client_socket.recv(2)
        if len(agree_header) >= 2:
            agree_type = struct.unpack('!H', agree_header)[0]#解包为无符号短整型，即Type=2
            print(f'Received agree: Type={agree_type}')
        else:
            print('Failed to receive agree packet')
            return
        
        # ========== 阶段4：循环发送数据块并接收反转结果 ==========
        reversed_parts = []  # 存储每个块的反转结果
        offset = 0  # 当前读取位置
        
        # 遍历每个数据块
        for i, block_size in enumerate(block_sizes, 1):#enumerate函数返回索引和元素,自动生成索引从1开始,方便打印
            # 从content中提取当前块的数据
            block_data = content[offset:offset + block_size]
            offset += block_size  # 更新读取位置
            
            # 构造 ReverseRequest 报文（Type=3，Length，Data）
            request_packet = struct.pack('!HI', 3, block_size) + block_data.encode('ascii')
            client_socket.sendall(request_packet)  # 发送请求
            print(f'Sent reverseRequest {i}: Length={block_size}')
            
            # 接收服务器的响应（ReverseAnswer）
            answer_header = client_socket.recv(6)
            if len(answer_header) >= 6:
                # 解析响应头部：Type=4，Length
                answer_type, data_len = struct.unpack('!HI', answer_header)
                
                # 接收反转后的数据（可能需要多次recv）
                reversed_data = b''
                while len(reversed_data) < data_len:
                    chunk = client_socket.recv(data_len - len(reversed_data))
                    if not chunk:
                        break
                    reversed_data += chunk
                #解决TCP粘包问题，防止数据丢失
                
                # 如果数据接收完整
                if len(reversed_data) == data_len:
                    # 解码为字符串并保存
                    reversed_str = reversed_data.decode('ascii')
                    reversed_parts.append(reversed_str)
                    print(f'{i}: {reversed_str}')  # 打印当前块的反转结果
                else:
                    print(f'Incomplete reverseAnswer for block {i}')
                    break
            else:
                print(f'Failed to receive reverseAnswer for block {i}')
                break
        
        # ========== 阶段5：关闭连接并保存结果 ==========
        client_socket.close()  # 关闭套接字
        
        # 将所有块的反转结果拼接成完整字符串
        full_reversed = ''.join(reversed_parts)
        
        # 构造输出文件名（在原文件名前加reversed_）
        output_file = 'reversed_' + file_path
        
        # 将完整反转结果写入文件
        with open(output_file, 'w', encoding='ascii') as f:
            f.write(full_reversed)
        
        # 输出最终结果信息
        print(f'\nFull reversed text written to {output_file}')
        print(f'Total reversed characters: {len(full_reversed)}')
        
    except Exception as e:
        # 捕获并打印异常
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

# 程序入口
if __name__ == '__main__':
    # 检查命令行参数数量是否正确
    if len(sys.argv) != 7:
        print('Usage: python reversetcpclient.py <server_ip> <server_port> <file_path> <Lmin> <Lmax> <chunk_seed>')
        print('Example: python reversetcpclient.py 127.0.0.1 8888 test.txt 50 100 42')
        sys.exit(1)  # 参数不正确，退出程序
    
    # 解析命令行参数
    server_ip = sys.argv[1]       # 服务器IP地址
    server_port = int(sys.argv[2])  # 服务器端口（转换为整数）
    file_path = sys.argv[3]      # 要反转的文件路径
    Lmin = int(sys.argv[4])      # 最小分块大小
    Lmax = int(sys.argv[5])      # 最大分块大小
    chunk_seed = int(sys.argv[6])  # 随机种子
    
    # 调用主函数
    main(server_ip, server_port, file_path, Lmin, Lmax, chunk_seed)