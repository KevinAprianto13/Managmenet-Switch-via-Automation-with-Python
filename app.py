from netmiko import ConnectHandler
import getpass
import time

# Fungsi untuk memilih vendor perangkat
def vendor_selection():
    print("\n=== Pilih Vendor ===")
    print("1. Cisco")
    print("2. Aruba")
    print("3. Dell")
    print("4. MikroTik")
    vendor = input("Pilih vendor [1-4]: ")

    if vendor == '1':
        return 'cisco_ios'
    elif vendor == '2':
        return 'aruba_os'
    elif vendor == '3':
        return 'dell_os'
    elif vendor == '4':
        return 'mikrotik'
    else:
        print("❌ Vendor tidak valid.")
        return None

# Fungsi untuk login ke perangkat
def connect_device(device_type):
    print("\n=== Login ke Switch ===")
    ip = input("IP Address: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    device = {
        'device_type': device_type,
        'ip': ip,
        'username': username,
        'password': password,
    }

    try:
        connection = ConnectHandler(**device)
        print("✅ Berhasil konek ke switch")
        return connection
    except Exception as e:
        print(f"❌ Gagal konek: {e}")
        return None

# Fungsi untuk konfigurasi Trunk Port
def trunk_port_config(device, vendor_type):
    port = input("Masukkan port (contoh 1/0/1): ")
    vlans = input("Masukkan VLAN yang diizinkan (misal: 10,20,30): ")

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        commands = [
            f"interface {port}",
            "switchport mode trunk",
            f"switchport trunk allowed vlan {vlans}",
            "no shutdown"
        ]
    elif vendor_type == 'aruba_os':
        commands = [
            f"interface {port}",
            f"vlan trunk allowed {vlans}",
            "no shutdown"
        ]
    elif vendor_type == 'mikrotik':
        commands = [
            f"/interface ethernet switch port set {port} vlan-mode=secure vlan-header=always-strip",
            f"/interface ethernet switch port vlan-member add vlan-id={vlans} ports={port}"
        ]
    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set(commands)
    print("✅ Trunk port dikonfigurasi.")

# Fungsi untuk konfigurasi VLAN Access
def vlan_access(device, vendor_type):
    vlan = input("Masukkan VLAN ID: ")
    nama_vlan = input("Masukkan nama VLAN: ")
    port = input("Masukkan port (contoh 1/0/1): ")

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        commands = [
            f"vlan {vlan}",
            f"name {nama_vlan}",
            f"interface {port}",
            "switchport mode access",
            f"switchport access vlan {vlan}",
            "no shutdown"
        ]
    elif vendor_type == 'aruba_os':
        commands = [
            f"vlan {vlan} name {nama_vlan}",
            f"interface {port}",
            f"vlan {vlan}",
            "no shutdown"
        ]
    elif vendor_type == 'mikrotik':
        commands = [
            f"/interface vlan add name={nama_vlan} vlan-id={vlan} interface=ether1",
            f"/interface ethernet switch port set {port} vlan-mode=secure vlan-header=always-strip",
            f"/interface ethernet switch port vlan-member add vlan-id={vlan} ports={port}"
        ]
    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set(commands)
    print("✅ VLAN Access dikonfigurasi.")

# Fungsi untuk konfigurasi Port Security
def port_security(device, vendor_type):
    port = input("Masukkan port (contoh 1/0/1): ")
    max_mac = input("Maksimum MAC address (contoh 1): ")
    sticky = input("Gunakan sticky MAC? (Y/n): ").lower()

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        commands = [
            f"interface {port}",
            "switchport mode access",
            "switchport port-security",
            f"switchport port-security maximum {max_mac}"
        ]
        if sticky == 'y' or sticky == '':
            commands.append("switchport port-security mac-address sticky")
    elif vendor_type == 'aruba_os':
        commands = [
            f"interface {port}",
            "port-access security",
            f"port-access security maximum {max_mac}"
        ]
        if sticky == 'y' or sticky == '':
            commands.append("port-access security mac-address sticky")
    elif vendor_type == 'mikrotik':
        commands = [
            f"/interface ethernet switch port set {port} security-mac-address-limit={max_mac}",
            f"/interface ethernet switch port set {port} security-mac-address-sticky={sticky}"
        ]
    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set(commands)
    print("✅ Port Security dikonfigurasi.")

# Fungsi untuk konfigurasi Spanning Tree Protocol (STP)
def stp_config(device, vendor_type):
    vlan = input("Masukkan VLAN ID untuk STP: ")
    priority = input("Masukkan priority (kelipatan 4096, contoh 24576): ")

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        command = f"spanning-tree vlan {vlan} priority {priority}"
    elif vendor_type == 'aruba_os':
        command = f"spanning-tree priority {priority}"
    elif vendor_type == 'mikrotik':
        command = f"/interface ethernet switch stp set {vlan} priority={priority}"
    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set([command])
    print("✅ STP dikonfigurasi.")

# Fungsi untuk mengganti hostname
def ganti_hostname(device, vendor_type):
    hostname = input("Masukkan hostname baru: ")

    if vendor_type in ['cisco_ios', 'aruba_os', 'dell_os']:
        command = f"hostname {hostname}"
    elif vendor_type == 'mikrotik':
        command = f"/system identity set name={hostname}"
    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set([command])
    print("✅ Hostname diganti.")

def save_config(device):
    try:
        time.sleep(1)  # Memberikan jeda waktu agar perangkat siap
        device.send_command("write memory")
        print("✅ Konfigurasi disimpan.")
    except Exception as e:
        print(f"❌ Gagal menyimpan konfigurasi: {str(e)}")


def access_list(device, vendor_type):
    acl_number = input("Masukkan nomor ACL (contoh: 10 atau 110): ")
    action = input("Masukkan Aturan (permit / deny): ").lower()
    source = input("Masukkan Source IP (contoh: 192.168.1.0 0.0.0.255 / any / host 192.168.1.10): ")
    protocol = input("Masukkan Protocol (ip / tcp / udp): ").lower()
    destination = input("Masukkan Destination IP (contoh: any / host 10.0.0.1): ")
    port = input("Masukkan port (kosongkan jika tidak perlu, contoh: eq 80): ")
    interface = input("Masukkan interface yang akan diberi ACL (contoh: FastEthernet0/1): ")
    direction = input("Masukkan arah ACL (in / out): ").lower()

    if vendor_type in ['cisco_ios', 'dell_os']:
        # Perintah untuk membuat ACL di Cisco
        acl_cmd = f"access-list {acl_number} {action} {source} {destination} {port}".strip()
        apply_cmd = [
            f"interface {interface}",
            f"ip access-group {acl_number} {direction}"  # Menggunakan perintah 'ip access-group' di Cisco
        ]
        # Kirim perintah ke perangkat Cisco
        device.send_config_set([acl_cmd] + apply_cmd)
        print("✅ ACL dikonfigurasi.")

    elif vendor_type == 'aruba_os':
        acl_name = f"ACL_{acl_number}"
        acl_cmd = [
            f"ip access-list extended {acl_name}",
            f" {action} {protocol} {source} {destination} {port}".strip(),
            "exit",
            f"interface {interface}",
            f"ip access-group {acl_name} {direction}"
        ]
        device.send_config_set(acl_cmd)
        print("✅ ACL dikonfigurasi.")

    elif vendor_type == 'mikrotik':
        mikrotik_chain = "forward"
        command = f"/ip firewall filter add chain={mikrotik_chain} src-address={source} dst-address={destination} protocol={protocol}"
        if port:
            command += f" dst-port={port.split()[-1]}"
        command += f" action={'accept' if action == 'permit' else 'drop'}"
        device.send_command(command)
        print("✅ ACL dikonfigurasi di Mikrotik.")

    else:
        print("❌ Vendor tidak valid.")
        return


#fungsi untuk hapus acl
def hapus_acl(device, vendor_type):
    acl_number = input("Masukkan nomor ACL yang ingin dihapus: ")
    interface = input("Masukkan nama interface yang terpasang ACL (contoh: FastEthernet0/1): ")
    direction = input("Masukkan arah ACL (in / out): ").lower()

    if vendor_type in ['cisco_ios', 'dell_os']:
        commands = [
            f"interface {interface}",
            f"no ip access-group {acl_number} {direction}",
            f"no access-list {acl_number}"  # Menghapus ACL
        ]

    elif vendor_type == 'aruba_os':
        acl_name = f"ACL_{acl_number}"
        commands = [
            f"interface {interface}",
            f"no ip access-group {acl_name} {direction}",
            f"no ip access-list extended {acl_name}"  # Menghapus ACL
        ]

    elif vendor_type == 'mikrotik':
        print("Daftar firewall filter saat ini:")
        filters = device.send_command("/ip firewall filter print")
        print(filters)
        rule_id = input("Masukkan nomor rule yang ingin dihapus (contoh: 0): ")
        commands = [f"/ip firewall filter remove {rule_id}"]  # Menghapus rule

    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set(commands)
    print("✅ ACL berhasil dihapus.")


# Fungsi utama
def main():
    vendor_type = vendor_selection()
    if not vendor_type:
        return

    device = connect_device(vendor_type)
    if not device:
        return

    while True:
        print("\n=== MENU SWITCH AUTOMATION ===")
        print("1. Konfigurasi VLAN Access")
        print("2. Konfigurasi Port Security")
        print("3. Konfigurasi STP")
        print("4. Konfigurasi Trunk Port")
        print("5. Ganti Hostname")
        print("6. Save Configuration")
        print("7. Konfigurasi Access-List")
        print("8. Hapus ACL")
        print("9. Keluar")
        

        choice = input("Pilih menu [1-9]: ")

        if choice == '1':
            vlan_access(device, vendor_type)
        elif choice == '2':
            port_security(device, vendor_type)
        elif choice == '3':
            stp_config(device, vendor_type)
        elif choice == '4':
            trunk_port_config(device, vendor_type)
        elif choice == '5':
            ganti_hostname(device, vendor_type)
        elif choice == '6':
            save_config(device)
        elif choice == '7':
            access_list(device, vendor_type)
        elif choice == '8':
            hapus_acl(device, vendor_type)
        elif choice == '9':
            print("Keluar.")
            break
        else:
            print("❌ Menu tidak valid.")

    device.disconnect()

if __name__ == "__main__":
    main()
