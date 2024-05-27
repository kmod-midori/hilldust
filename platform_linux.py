import hillstone

import subprocess
import binascii

del_commands = []

def setup_network_internal(c: hillstone.ClientCore, local_ip: str, local_port: int, routes: list[str]):
    global del_commands

    del_commands.append(["ip", "xfrm", "state", "deleteall"])
    subprocess.check_call([
        "ip", "xfrm", "state", "add",
        "src", local_ip, "dst", str(c.server_host),
        "proto", "esp", "spi", hex(c.ipsec_param.out_spi), "reqid", "256", "mode", "tunnel", "if_id", "233",
        "auth-trunc", "hmac(md5)", f"0x{binascii.hexlify(c.ipsec_param.out_auth_key).decode()}", "96",
        "enc", "cbc(aes)", f"0x{binascii.hexlify(c.ipsec_param.out_crypt_key).decode()}",
        "encap", "espinudp", str(local_port), str(c.server_udp_port), "0.0.0.0"
    ])

    subprocess.check_call([
        "ip", "xfrm", "state", "add",
        "src", str(c.server_host), "dst", local_ip,
        "proto", "esp", "spi", hex(c.ipsec_param.in_spi), "reqid", "256", "mode", "tunnel", "if_id", "233",
        "auth-trunc", "hmac(md5)", f"0x{binascii.hexlify(c.ipsec_param.in_auth_key).decode()}", "96",
        "enc", "cbc(aes)", f"0x{binascii.hexlify(c.ipsec_param.in_crypt_key).decode()}",
        "encap", "espinudp", str(c.server_udp_port), str(local_port), "0.0.0.0"
    ])
    

    del_commands.append(["ip", "xfrm", "policy", "deleteall"])
    subprocess.check_call([
        "ip", "xfrm", "policy", "add",
        "src", "0.0.0.0/0", "dst", "0.0.0.0/0", "dir", "out",
        "tmpl",
        "dst", str(c.server_host),
        "proto", "esp", "mode", "tunnel", "reqid", "256",
        "if_id", "233"
    ])
    subprocess.check_call([
        "ip", "xfrm", "policy", "add",
        "src", "0.0.0.0/0", "dst", "0.0.0.0/0", "dir", "in",
        "tmpl",
        "src", str(c.server_host), 
        "proto", "esp", "mode", "tunnel", "reqid", "256",
        "if_id", "233"
    ])
    

    del_commands.append(["ip", "link", "delete", "ipsec0"])
    subprocess.check_call([
        "ip", "link", "add", "ipsec0", "type", "xfrm", "dev", "lo", "if_id", "233"
    ])
    subprocess.check_call([
        "ip", "addr", "add", "dev", "ipsec0", str(c.ip_ipv4)
    ])
    subprocess.check_call([
        "ip", "link", "set", "ipsec0", "up"
    ])

    for route in routes:
        subprocess.check_call(["ip", "route", "add", route, "via", str(c.gateway_ipv4)])


def set_network(c: hillstone.ClientCore, local_ip: str, local_port: int, routes: list[str]):
    try:
        setup_network_internal(c, local_ip, local_port, routes)
    except:
        restore_network(c)
        raise

def restore_network(c: hillstone.ClientCore):
    global del_commands
    for cmd in del_commands:
        subprocess.call(cmd)
