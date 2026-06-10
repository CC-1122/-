TCP Socket 编程实验作业
================================

1. 文件列表
--------
- reversetcpserver.py    - TCP 服务器程序
- reversetcpclient.py    - TCP 客户端程序
- test.txt               - 测试输入文件（ASCII 文本）
- readme.txt             - 本说明文档
- run_log.txt            - 运行时日志文件（服务器自动生成）
- reversed_test.txt      - 反转结果输出文件（客户端自动生成）

2. 运行环境要求
---------------
- Python 3.x（建议使用 Python 3.6 及以上版本）
- 操作系统：Windows / Linux / macOS
- 无需额外安装第三方库（仅使用 Python 标准库）

3. 运行说明
-----------------------

3.1 启动服务器：
   python reversetcpserver.py [端口号]
   
   示例：
   python reversetcpserver.py 8888
   
   如果不指定端口号，默认使用 8888 端口。

3.2 启动客户端：
   python reversetcpclient.py <服务器IP> <服务器端口> <文件路径> <Lmin> <Lmax> <chunk_seed>
   
   示例：
   python reversetcpclient.py 127.0.0.1 8888 test.txt 50 100 42
   
   参数说明：
   - server_ip: 服务器的 IP 地址（如 127.0.0.1 表示本地）
   - server_port: 服务器监听的端口号
   - file_path: 需要反转的 ASCII 文本文件路径
   - Lmin: 分块的最小字节数
   - Lmax: 分块的最大字节数
   - chunk_seed: 随机分块的种子（用于生成可重现的分块大小）

3.3 测试步骤：
   1. 打开终端窗口，启动服务器
   2. 打开另一个终端窗口，运行客户端
   3. 客户端会输出每个块的反转结果，并将完整结果保存到 reversed_xxx.txt 文件

4. 协议规范
-------------------------

4.1 报文类型：
   - Type=1: Initialization（客户端 → 服务器）- 初始化请求
   - Type=2: Agree（服务器 → 客户端）- 确认接收
   - Type=3: ReverseRequest（客户端 → 服务器）- 发送待反转数据
   - Type=4: ReverseAnswer（服务器 → 客户端）- 返回反转后数据

4.2 报文格式：
   Initialization（Type=1）:
     +--------+--------+
     | Type   | N      |
     | 2字节  | 4字节  |
     +--------+--------+
     N = 需要反转的数据块数量
   
   Agree（Type=2）:
     +--------+
     | Type   |
     | 2字节  |
     +--------+
   
   ReverseRequest（Type=3）:
     +--------+--------+--------+
     | Type   | Length | Data   |
     | 2字节  | 4字节  | N字节  |
     +--------+--------+--------+
     Length = Data 字段的长度
   
   ReverseAnswer（Type=4）:
     +--------+--------+-------------+
     | Type   | Length | reverseData |
     | 2字节  | 4字节  | N字节       |
     +--------+--------+-------------+
     Length = reverseData 字段的长度

5. 分块算法说明
---------------------------
客户端使用以下算法将文件分割成多个数据块：
1. 初始化 remaining = 文件总大小
2. 当 remaining > 0 时：
   如果 remaining <= Lmin:
      block_size = remaining
   否则:
      block_size = 随机数(Lmin, min(Lmax, remaining))
   将 block_size 添加到分块列表
   remaining -= block_size
3. 返回分块大小列表

**注意**：使用指定的 chunk_seed 可以保证分块结果可重现，便于验证。

6. 功能特点
-----------
- **多线程服务器**：支持同时处理多个客户端请求
- **运行日志记录**：自动生成 run_log.txt，包含毫秒级时间戳
- **自定义报文结构**：通过 Type 和 Length 字段实现协议解析
- **随机分块**：根据参数动态生成分块大小
- **ASCII 文本反转**：对收到的数据进行字符级反转
- **错误处理**：包含连接异常、数据不完整等边界情况处理

7. 输入输出示例
-----------------
客户端运行示例：
```
File size: 380 bytes
Number of blocks: 6
Block sizes: [90, 57, 51, 97, 67, 18]
Sent Initialization: Type=1, N=6
Received agree: Type=2
1: w nus ehT.ylippah gnignis drib lufituaeb a was eH
2: .eert llat a pu debmilc yeknom elttil A
3: Amag gniyalp erew nerdlihC
4: .skrap eht ni semag
...
Full reversed text written to reversed_test.txt
Total reversed characters: 380
```

8. Wireshark 抓包验证
-----------------------
可以使用 Wireshark 验证网络报文：
1. 打开 Wireshark，选择回环接口（Loopback）
2. 设置过滤条件：tcp port 8888
3. 运行服务器和客户端
4. 在 Wireshark 中可以看到：
   - TCP 三次握手（SYN → SYN-ACK → ACK）
   - Initialization 报文（6字节）
   - Agree 报文（2字节）
   - ReverseRequest 和 ReverseAnswer 报文
   - TCP 四次挥手（FIN → FIN-ACK → ACK）

9. 常见问题
-----------
Q: 客户端连接失败？
A: 请确保服务器已启动，并且 IP 地址和端口号正确。

Q: 文件反转结果不正确？
A: 请确保输入文件只包含 ASCII 可打印字符。

Q: 如何停止服务器？
A: 在服务器终端按 Ctrl+C 即可停止。

10. 项目结构
-------------
```
├── reversetcpserver.py    # TCP 服务器
├── reversetcpclient.py    # TCP 客户端
├── test.txt               # 测试文件
├── readme.txt             # 说明文档
├── run_log.txt            # 运行日志（自动生成）
└── reversed_test.txt      # 输出文件（自动生成）
```

---
作者：学生作业
日期：2026年6月
