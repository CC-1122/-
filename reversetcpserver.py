# TCP Socket 服务器程序
# 功能：接收客户端发送的数据块，进行反转处理后返回
# 支持多线程并发处理多个客户端

# 导入需要的模块
import socket       # 用于网络通信
import threading    # 用于多线程处理
import struct       # 用于数据打包/解包（网络字节序）
import time         # 用于时间戳
import os           # 用于文件操作

# 日志文件名称常量
LOG_FILE = 'run_log.txt'

def log_message(msg):
    """
    记录运行日志到文件
    :param msg: 要记录的日志消息
    """
    # 获取当前时间（精确到毫秒）
    now = time.localtime()
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', now)  # 格式化时间
    ms = int(time.time() * 1000) % 1000  # 获取毫秒部分，0.123456。123是毫秒部分
    timestamp = f'{timestamp}.{ms:03d}'  # 组合成完整的时间戳，格式化拼接，不足3位用0填充
    
    # 追加写入日志文件
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {msg}\n')

def reverse_text(data):
    """
    反转字符串
    :param data: 输入的字符串
    :return: 反转后的字符串
    """
    return data[::-1]  # Python切片语法：[::-1] 表示逆序

def handle_client(client_socket, client_addr):
    """
    处理单个客户端连接的核心逻辑
    :param client_socket: 客户端套接字对象
    :param client_addr: 客户端地址（IP, 端口）
    """
    # 记录新客户端连接
    log_message(f'New client connected: {client_addr}')
    
    try:
        # ========== 阶段1：接收初始化报文 ==========
        # 接收 Initialization 报文头部（6字节：Type=2字节 + N=4字节）
        header = client_socket.recv(6)
        # 如果没有收到完整的头部，说明客户端断开连接
        if len(header) < 6:
            log_message(f'Client {client_addr} disconnected (no header)')
            return
        
        # 解析报文：Type=1表示初始化，N表示数据块数量
        # '!HI' 表示网络字节序（!），H=无符号短整型（2字节），I=无符号整型（4字节）
        type_field, n_blocks = struct.unpack('!HI', header)
        log_message(f'Received Initialization from {client_addr}: Type={type_field}, N={n_blocks}')
        
        # ========== 阶段2：发送确认报文 ==========
        # 构造 Agree 报文（Type=2，2字节）
        agree_packet = struct.pack('!H', 2)
        client_socket.sendall(agree_packet)  # 发送确认
        log_message(f'Sent agree to {client_addr}')
        
        # ========== 阶段3：循环处理每个数据块 ==========
        for block_num in range(1, n_blocks + 1):
            # 接收 ReverseRequest 报文头部（6字节）
            header = client_socket.recv(6)
            if len(header) < 6:
                log_message(f'Client {client_addr} disconnected during transfer')
                break
            
            # 解析头部：Type=3表示反转请求，Length表示数据长度
            type_field, length = struct.unpack('!HI', header)
            log_message(f'Received reverseRequest from {client_addr}: Type={type_field}, Length={length}')
            
            # 接收实际数据（可能需要多次recv才能接收完整）
            data = b''  # 存储接收到的数据
            while len(data) < length:
                # 接收剩余长度的数据
                chunk = client_socket.recv(length - len(data))
                if not chunk:  # 如果没有收到数据，说明连接断开
                    break
                data += chunk  # 累加数据
            
            # 如果数据接收完整
            if len(data) == length:
                # 将字节数据解码为ASCII字符串，反转后再编码回字节
                reversed_data = reverse_text(data.decode('ascii')).encode('ascii')
                reversed_len = len(reversed_data)
                
                # 构造 ReverseAnswer 报文（Type=4，Length，反转后的数据）
                answer_packet = struct.pack('!HI', 4, reversed_len) + reversed_data
                client_socket.sendall(answer_packet)  # 发送反转结果
                log_message(f'Sent reverseAnswer to {client_addr}: Length={reversed_len}')
            else:
                # 数据不完整，记录错误并退出循环
                log_message(f'Incomplete data from {client_addr}, expected {length}, got {len(data)}')
                break
        
    except Exception as e:
        # 捕获异常并记录日志
        log_message(f'Error handling client {client_addr}: {str(e)}')
    finally:
        # 无论是否发生异常，都要关闭客户端套接字
        client_socket.close()
        log_message(f'Client {client_addr} disconnected')

def main(port=8888):
    """
    服务器主函数
    :param port: 监听端口，默认8888
    """
    # 创建TCP套接字
    # socket.AF_INET: IPv4地址族
    # socket.SOCK_STREAM: TCP协议
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # 设置套接字选项：SO_REUSEADDR允许端口快速重用
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # 绑定地址和端口：'0.0.0.0'表示监听所有网络接口
    server_socket.bind(('0.0.0.0', port))
    
    # 开始监听，最大等待队列长度为5
    server_socket.listen(5)
    
    # 如果日志文件已存在，删除旧日志
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    # 记录服务器启动日志
    log_message(f'Server started on port {port}')
    print(f'Server listening on port {port}...')
    
    try:
        # 主循环：不断接受新的客户端连接
        while True:
            # accept() 阻塞等待客户端连接
            # 返回：(客户端套接字, 客户端地址)
            client_socket, client_addr = server_socket.accept()
            
            # 创建新线程处理客户端，避免阻塞主线程
            # 每个客户端独立一个线程
            client_thread = threading.Thread(
                target=handle_client,  # 线程执行的函数
                args=(client_socket, client_addr)  # 传递给函数的参数
            )
            client_thread.start()  # 启动线程
    
    except KeyboardInterrupt:
        # 捕获Ctrl+C，优雅关闭服务器
        log_message('Server shutting down')
        print('Server shutting down...')
    finally:
        # 关闭服务器套接字
        server_socket.close()

# 程序入口
if __name__ == '__main__':
    import sys
    # 从命令行参数获取端口号，如果没有指定则使用默认8888
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    main(port)