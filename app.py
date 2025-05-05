from netmiko import ConnectHandler
import getpass
import time
import json
import random
from difflib import get_close_matches
from colorama import init, Fore, Back, Style

# Fungsi untuk memilih vendor perangkat
def vendor_selection():
    while True:  # Loop agar bisa kembali ke menu pemilihan vendor jika ada kesalahan
        try:
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
                continue  # Jika input salah, minta input ulang
        except KeyboardInterrupt:
            print("\nOperasi dibatalkan. Kembali ke menu utama...")
            return None  # Mengembalikan None untuk kembali ke menu utama

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
    descriptions = input("Masukan Descriptions Interface (contoh IT/HRD/etc): ")

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        commands = [
            f"vlan {vlan}",
            f"name {nama_vlan}",
            f"interface {port}",
            "switchport mode access",
            f"switchport access vlan {vlan}",
            f"description {descriptions}",
            "no shutdown"
        ]
    elif vendor_type == 'aruba_os':
        commands = [
            f"vlan {vlan} name {nama_vlan}",
            f"interface {port}",
            f"description {descriptions}",
            f"vlan access {vlan}",
            "no shutdown"
        ]
    elif vendor_type == 'mikrotik':
        commands = [
            f"/interface vlan add name={nama_vlan} vlan-id={vlan} interface=ether1",
            f"/interface ethernet set [find name={port}] comment=\"{descriptions}\"",
            f"/interface ethernet switch port set {port} vlan-mode=secure vlan-header=always-strip",
            f"/interface ethernet switch vlan add vlan-id={vlan} ports={port}"
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
    violation = input("Tindakan pelanggaran (shutdown/protect/restrict): ").lower()
    aging_time = input("Waktu aging (menit, contoh 5): ")

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        commands = [
            f"interface {port}",
            "switchport mode access",
            "switchport port-security",
            f"switchport port-security maximum {max_mac}",
            f"switchport port-security aging time {aging_time}",
            f"switchport port-security violation {violation}"
        ]
        if sticky == 'y' or sticky == '':
            commands.append("switchport port-security mac-address sticky")
    
    elif vendor_type == 'aruba_os':
        commands = [
            f"interface {port}",
            "port-access security",
            f"port-access security maximum {max_mac}",
            f"port-access security aging time {aging_time}",
            f"port-access security violation {violation}"
        ]
        if sticky == 'y' or sticky == '':
            commands.append("port-access security mac-address sticky")
    
    elif vendor_type == 'mikrotik':
        # MikroTik memiliki format yang sedikit berbeda
        commands = [
            f"/interface ethernet switch port set {port} security-mac-address-limit={max_mac}",
            f"/interface ethernet switch port set {port} security-mac-address-sticky={sticky}",
            f"/interface ethernet switch port set {port} security-aging-time={aging_time}",
        ]
        if violation == "shutdown":
            commands.append(f"/interface ethernet switch port set {port} security-violation=drop")
        elif violation == "restrict":
            commands.append(f"/interface ethernet switch port set {port} security-violation=reject")
        elif violation == "protect":
            commands.append(f"/interface ethernet switch port set {port} security-violation=protect")
        else:
            print("❌ Tindakan pelanggaran tidak valid. Gunakan 'shutdown', 'protect', atau 'restrict'.")
            return

    else:
        print("❌ Vendor tidak valid.")
        return

    # Mengirimkan konfigurasi ke perangkat
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

def save_config(device, vendor_type):
    try:
        time.sleep(1)  # Jeda agar perangkat siap

        if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
            device.send_command("write memory")
        elif vendor_type == 'aruba_os':
            device.send_command("write memory")  # Aruba OS CLI juga sering pakai ini
        elif vendor_type == 'mikrotik':
            device.send_command("/system backup save name=config-backup")
        else:
            print("❌ Vendor tidak dikenali.")
            return

        print("✅ Konfigurasi disimpan.")
    except Exception as e:
        print(f"❌ Gagal menyimpan konfigurasi: {str(e)}")



def access_list(device, vendor_type):
    acl_number = input("Masukkan nomor ACL (contoh: 10 atau 110): ").strip()
    action = input("Masukkan Aturan (permit / deny): ").lower()
    protocol = input("Masukkan Protocol (ip / tcp / udp): ").lower()

    # Source
    source = input("Masukkan Source IP (contoh: 192.168.1.0 / any / host 192.168.1.10): ").strip()
    if source not in ["any"] and not source.startswith("host"):
        wildcard_source = input("Masukkan wildcard bits untuk source (contoh: 0.0.0.255): ").strip()
        source = f"{source} {wildcard_source}"

    # Destination
    destination = input("Masukkan Destination IP (contoh: 10.0.0.0 / any / host 10.0.0.1): ").strip()
    if destination not in ["any"] and not destination.startswith("host"):
        wildcard_destination = input("Masukkan wildcard bits untuk destination (contoh: 0.0.0.255): ").strip()
        destination = f"{destination} {wildcard_destination}"

    # Port hanya jika TCP/UDP
    port = ""
    if protocol in ["tcp", "udp"]:
        port = input("Masukkan port (kosongkan jika tidak perlu, contoh: eq 80): ").strip()

    interface = input("Masukkan interface yang akan diberi ACL (contoh: FastEthernet0/1): ").strip()
    direction = input("Masukkan arah ACL (in / out): ").lower()

    if vendor_type in ['cisco_ios', 'dell_os']:
        commands = []

        if int(acl_number) < 100:
            # Standard ACL hanya source
            acl_cmd = f"access-list {acl_number} {action} {source}".strip()
        else:
            # Extended ACL lengkap
            acl_cmd = f"access-list {acl_number} {action} {protocol} {source} {destination} {port}".strip()

        commands.append(acl_cmd)
        commands.append(f"interface {interface}")
        commands.append(f"ip access-group {acl_number} {direction}")
        device.send_config_set(commands)
        print("✅ ACL dikonfigurasi untuk Cisco/Dell.")

    elif vendor_type == 'aruba_os':
        acl_name = f"ACL_{acl_number}"
        acl_lines = [f"ip access-list extended {acl_name}"]

        rule = f" {action} {protocol} {source} {destination}"
        if port:
            rule += f" {port}"
        acl_lines.append(rule.strip())
        acl_lines.append("exit")
        acl_lines.append(f"interface {interface}")
        acl_lines.append(f"ip access-group {acl_name} {direction}")
        device.send_config_set(acl_lines)
        print("✅ ACL dikonfigurasi untuk Aruba.")

    elif vendor_type == 'mikrotik':
        mikrotik_chain = "forward"
        command = f"/ip firewall filter add chain={mikrotik_chain} src-address={source.split()[0]} dst-address={destination.split()[0]} protocol={protocol}"
        if port:
            command += f" dst-port={port.split()[-1]}"
        command += f" action={'accept' if action == 'permit' else 'drop'}"
        device.send_command(command)
        print("✅ ACL dikonfigurasi di Mikrotik.")

    else:
        print("❌ Vendor tidak valid.")



def hapus_acl(device, vendor_type):
    print("\n📌 Kamu bisa memilih untuk menghapus ACL dari interface, atau dari konfigurasi ACL-nya, atau keduanya.")

    acl_number = input("Masukkan nomor ACL: ").strip()
    interface = input("Masukkan nama interface yang terpasang ACL (biarkan kosong jika tidak ingin menghapus dari interface): ").strip()

    commands = []

    if interface:
        direction = input("Masukkan arah ACL (in / out): ").lower()
        if direction not in ['in', 'out']:
            print("❌ Arah ACL tidak valid. Gunakan 'in' atau 'out'.")
            return

        konfirmasi = input(f"Yakin ingin menghapus ACL {acl_number} dari interface {interface} arah {direction}? (y/n): ").lower()
        if konfirmasi == 'y':
            if vendor_type in ['cisco_ios', 'dell_os']:
                commands += [
                    f"interface {interface}",
                    f"no ip access-group {acl_number} {direction}"
                ]
            elif vendor_type == 'aruba_os':
                acl_name = f"ACL_{acl_number}"
                commands += [
                    f"interface {interface}",
                    f"no ip access-group {acl_name} {direction}"
                ]

    # Tanya apakah ACL-nya juga ingin dihapus dari konfigurasi
    hapus_acl_global = input("Apakah kamu juga ingin menghapus rule ACL dari konfigurasi (y/n)? ").lower()
    if hapus_acl_global == 'y':
        if vendor_type in ['cisco_ios', 'dell_os']:
            commands.append(f"no access-list {acl_number}")
        elif vendor_type == 'aruba_os':
            acl_name = f"ACL_{acl_number}"
            commands.append(f"no ip access-list extended {acl_name}")

    # Eksekusi
    if commands:
        try:
            output = device.send_config_set(commands)
            print(output)
            print("✅ Proses penghapusan selesai.")
        except Exception as e:
            print(f"❌ Gagal: {e}")
    else:
        print("ℹ️ Tidak ada perintah yang dijalankan.")

# Fungsi untuk menampilkan status dan konfigurasi perangkat
def show_device_status(device, vendor_type):
    print("\n=== Menampilkan Status dan Konfigurasi ===")

    # Perintah untuk vendor Cisco, Aruba, Dell, MikroTik
    if vendor_type == 'cisco_ios':
        commands = [
            "show interface brief",
            "show vlan brief",
            "show interface trunk",
            "show running-config"
        ]
    elif vendor_type == 'aruba_os':
        commands = [
            "show interface brief",
            "show vlan brief",
            "show interface trunk",
            "show running-config"
        ]
    elif vendor_type == 'dell_os':
        commands = [
            "show interface brief",
            "show vlan brief",
            "show interface trunk",
            "show running-config"
        ]
    elif vendor_type == 'mikrotik':
        commands = [
            "/interface print",
            "/interface vlan print",
            "/interface ethernet print",
            "/interface print"
        ]
    else:
        print("❌ Vendor tidak valid.")
        return

    # Eksekusi perintah dan tampilkan hasilnya
    try:
        for command in commands:
            print(f"\n=== Hasil perintah: {command} ===")
            output = device.send_command(command)
            print(output)
    except Exception as e:
        print(f"❌ Gagal menampilkan status: {e}")


def configure_ntp(device, vendor_type):
    ntp_server = input("Masukkan NTP server IP: ")

    if vendor_type == 'cisco_ios' or vendor_type == 'dell_os':
        commands = [
            f"ntp server {ntp_server}"
        ]
    elif vendor_type == 'aruba_os':
        commands = [
            f"ntp server {ntp_server}"
        ]
    elif vendor_type == 'mikrotik':
        commands = [
            f"/system ntp client set enabled=yes server={ntp_server}"
        ]
    else:
        print("❌ Vendor tidak valid.")
        return

    device.send_config_set(commands)
    print("✅ NTP server dikonfigurasi.")

def configure_bpdu_guard(connection, vendor):
    interface = input("Masukkan nama interface yang akan dikonfigurasi (contoh: GigabitEthernet1/0/10): ")

    if vendor == "cisco":
        commands = [
            f"interface {interface}",
            "spanning-tree bpduguard enable"
        ]
    elif vendor == "aruba":
        commands = [
            f"interface {interface}",
            "spanning-tree bpdu-protection"
        ]
    elif vendor == "dell":
        commands = [
            f"interface {interface}",
            "spanning-tree bpduguard"
        ]
    elif vendor == "mikrotik":
        commands = [
            "/interface bridge filter add chain=input protocol=stp action=drop",
            "/interface bridge filter add chain=input protocol=rstp action=drop",
            "/interface bridge filter add chain=input protocol=mstp action=drop"
        ]
    else:
        print("❌ Vendor tidak dikenali.")
        return

    try:
        output = connection.send_config_set(commands)
        print("✅ BPDU Guard berhasil dikonfigurasi.")
        print(output)
    except Exception as e:
        print(f"❌ Gagal mengatur BPDU Guard: {e}")






# Fungsi utama
def main():
    while True:  # Loop untuk memungkinkan mencoba kembali dari menu utama
        vendor_type = vendor_selection()
        if not vendor_type:
            print("Operasi dibatalkan. Kembali ke menu utama...")
            continue  # Jika vendor selection gagal atau Ctrl+C, kembali ke pemilihan vendor

        device = connect_device(vendor_type)
        if not device:
            print("Gagal terhubung ke perangkat. Kembali ke menu utama...")
            continue  # Jika gagal terhubung, kembali ke pemilihan vendor

        while True:
            try:
                print("\n=== MENU SWITCH AUTOMATION ===")
                print("1. Konfigurasi VLAN Access")
                print("2. Konfigurasi Port Security")
                print("3. Konfigurasi STP")
                print("4. Konfigurasi Trunk Port")
                print("5. Ganti Hostname")
                print("6. Save Configuration")
                print("7. Konfigurasi Access-List")
                print("8. Hapus ACL")
                print("9. Tampilkan Status dan Konfigurasi")
                print("10. NTP Konfigurasi")
                print("11. BPDU Konfigurasi")
                print("12. Keluar")

                choice = input("Pilih menu [1-11]: ")

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
                    save_config(device, vendor_type)
                elif choice == '7':
                    access_list(device, vendor_type)
                elif choice == '8':
                    hapus_acl(device, vendor_type)
                elif choice == '9':
                    show_device_status(device, vendor_type)
                elif choice == '10':
                    configure_ntp(device, vendor_type)
                elif choice == '11':
                    configure_bpdu_guard(device, vendor_type)
                elif choice == '12':
                    print("Keluar.")
                    device.disconnect()  # Disconnect setelah keluar dari menu
                    break  # Keluar dari menu ini dan kembali ke pemilihan vendor
                else:
                    print("❌ Menu tidak valid.")
            except KeyboardInterrupt:
                print("\nCtrl+C terdeteksi. Kembali ke menu Switch Automation...")
                continue  # Kembali ke menu Switch Automation tanpa keluar ke menu vendor

        print("\nKembali ke menu utama...\n")  # Setelah keluar dari perangkat, kembali ke menu vendor

if __name__ == "__main__":
    main()
