import socket
import struct

def build_dns_query(domain):
    # Transaction ID: 2 bytes
    transaction_id = b'\xaa\xaa'

    # Flags: 2 bytes
    flags = b'\x01\x00'  # 标准查询，递归

    # Questions: 2 bytes
    qdcount = b'\x00\x01'

    # Answer RRs, Authority RRs, Additional RRs: 6 bytes
    other_counts = b'\x00\x00\x00\x00\x00\x00'

    # 构建 Header
    header = transaction_id + flags + qdcount + other_counts

    # 构建 Question
    # 将域名分割为标签，并前缀长度
    qname = b''.join((bytes([len(label)]) + label.encode() for label in domain.split('.'))) + b'\x00'

    # QType: 2 bytes (A record)
    qtype = b'\x00\x01'

    # QClass: 2 bytes (IN)
    qclass = b'\x00\x01'

    question = qname + qtype + qclass

    return header + question

def parse_dns_response(response):
    # 跳过头部（12字节）
    header = response[:12]
    qdcount = struct.unpack('!H', header[4:6])[0]
    ancount = struct.unpack('!H', header[6:8])[0]

    # 跳过问题部分
    offset = 12
    for _ in range(qdcount):
        while response[offset] != 0:
            length = response[offset]
            offset += length + 1
        offset += 5  # 跳过 null 字节和 QTYPE, QCLASS

    # 解析回答部分
    ips = []
    for _ in range(ancount):
        # 跳过 NAME（通常是压缩格式，以指针开始）
        if response[offset] & 0xC0 == 0xC0:
            offset += 2
        else:
            while response[offset] != 0:
                length = response[offset]
                offset += length + 1
            offset += 1

        # TYPE, CLASS, TTL, RDLENGTH
        type_, class_, ttl, rdlength = struct.unpack('!HHIH', response[offset:offset+10])
        offset += 10

        if type_ == 1 and class_ == 1:  # A record
            ip = socket.inet_ntoa(response[offset:offset+4])
            ips.append(ip)
        offset += rdlength

    return ips

def dns_query(domain, dns_server='8.8.8.8', port=53):
    query = build_dns_query(domain)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        print(query)
        sock.sendto(query, (dns_server, port))
        response, _ = sock.recvfrom(512)
        print(f"收到响应: {response}")
        ips = parse_dns_response(response)
        if ips:
            print(f"{domain} 的 IP 地址:")
            for ip in ips:
                print(ip)
        else:
            print("未找到 IP 地址。")
    except socket.timeout:
        print("查询超时。")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    domain = "www.baidu.com"
    dns_server = '8.8.8.8'
    dns_query(domain, dns_server)
