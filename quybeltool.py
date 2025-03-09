import os
import requests
import json
import time
import subprocess
import asyncio
import aiohttp
import threading
import psutil
import uuid
import hashlib
from colorama import init, Fore, Style
import sys
import select

init()

SERVER_LINKS_FILE = "Private_Link.txt"
ACCOUNTS_FILE = "Account.txt"
CONFIG_FILE = "Config.json"
webhook_url = None
device_name = None
interval = None
stop_webhook_thread = False
webhook_thread = None
FLASK_SERVER_URL = ''
exit_flag = threading.Event()  # Biến để báo hiệu thoát

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    header = (
        Fore.CYAN + "╔════════════════════════════════════╗\n" +
        "║       Quy Bel Tool v1.0            ║\n" +
        "║   Auto Rejoin Roblox - Termux      ║\n" +
        "╚════════════════════════════════════╝\n" + Style.RESET_ALL +
        Fore.MAGENTA + " Chào mừng đến quy bel tool!\n" + Style.RESET_ALL
    )
    print(header)

def print_status_table(accounts, previous_status=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()
    table = (
        Fore.YELLOW + "╔════════════════════════════════════════════╗\n" +
        "║           TRẠNG THÁI HIỆN TẠI             ║\n" +
        "╠══════════════════════╦═════════════════════╣\n" +
        f"║ Roblox Game Rejoin   ║ {Fore.GREEN}Đang hoạt động{Style.RESET_ALL + Fore.YELLOW}    ║\n" +
        "╚══════════════════════╩═════════════════════╝\n" + Style.RESET_ALL
    )
    print(table)
    
    if previous_status is None:
        previous_status = {}
    print(Fore.CYAN + " Danh sách tài khoản:" + Style.RESET_ALL)
    for package_name, user_id in accounts:
        username = get_username(user_id) or user_id
        status = check_user_online(user_id)
        status_text = "Đang chơi" if status == 2 else "Đang chờ" if status == 1 else "Offline"
        color = Fore.GREEN if status == 2 else Fore.YELLOW if status == 1 else Fore.RED
        if previous_status.get(user_id) != status_text:
            print(f" - {package_name:<20} | {username:<15} | {color}{status_text}{Style.RESET_ALL}")
            previous_status[user_id] = status_text
    print(Fore.YELLOW + "═════════════════════════════════════════════" + Style.RESET_ALL)
    time.sleep(5)  # Chờ 5 giây để đọc bảng trạng thái
    return previous_status

def print_account_list(accounts, server_links):
    global exit_flag
    exit_flag.clear()  # Reset cờ thoát
    os.system('cls' if os.name == 'nt' else 'clear')
    print_header()
    print(Fore.CYAN + "╔═════ DANH SÁCH TÀI KHOẢN ═════╗" + Style.RESET_ALL)
    for (package_name, user_id), (_, server_link) in zip(accounts, server_links):
        username = get_username(user_id) or user_id
        status = check_user_online(user_id)
        status_text = "Đang chơi" if status == 2 else "Đang chờ" if status == 1 else "Offline"
        color = Fore.GREEN if status == 2 else Fore.YELLOW if status == 1 else Fore.RED
        print(Fore.CYAN + f" - Gói: {package_name:<20} | Tên: {username:<15} | ID: {user_id:<10} | Server: {server_link:<30} | {color}{status_text}{Style.RESET_ALL}")
    print(Fore.CYAN + "╚════════════════════════════════╝" + Style.RESET_ALL)
    print(Fore.MAGENTA + "Quay lại menu sau 10 giây hoặc nhấn Enter để quay lại ngay..." + Style.RESET_ALL)

    def countdown():
        time.sleep(10)  # Chờ 10 giây
        if not exit_flag.is_set():  # Nếu chưa nhấn Enter
            exit_flag.set()  # Đặt cờ để thoát

    # Chạy đồng hồ đếm ngược trong một thread riêng
    timer_thread = threading.Thread(target=countdown)
    timer_thread.start()

    # Chờ người dùng nhấn Enter
    while not exit_flag.is_set():
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()  # Đọc Enter
            exit_flag.set()  # Đặt cờ để thoát ngay
        time.sleep(0.1)  # Giảm tải CPU

    timer_thread.join()  # Đợi thread đếm ngược kết thúc

def get_device_hwid():
    hwid = str(uuid.uuid1())
    hwid_hash = hashlib.sha256(hwid.encode()).hexdigest()
    return hwid_hash

def notify_flask_server(hwid):
    data = {"hwid": hwid}
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(FLASK_SERVER_URL, json=data, headers=headers)
    except Exception:
        pass

def get_roblox_packages():
    packages = []
    result = subprocess.run("pm list packages | grep 'roblox'", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        packages = [line.split(":")[1] for line in result.stdout.splitlines()]
    return packages

def capture_screenshot():
    screenshot_path = "/data/data/com.termux/files/home/screenshot.png"
    os.system(f"screencap -p {screenshot_path}")
    return screenshot_path

def get_system_info():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    uptime = time.time() - psutil.boot_time()
    return {"cpu_usage": cpu_usage, "memory_total": memory_info.total, "memory_available": memory_info.available,
            "memory_used": memory_info.used, "uptime": uptime}

def load_config():
    global webhook_url, device_name, interval
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            webhook_url = config.get("webhook_url")
            device_name = config.get("device_name")
            interval = config.get("interval")
    else:
        webhook_url = device_name = interval = None

def save_config():
    config = {"webhook_url": webhook_url, "device_name": device_name, "interval": interval}
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def start_webhook_thread():
    global webhook_thread, stop_webhook_thread
    if webhook_thread is None or not webhook_thread.is_alive():
        stop_webhook_thread = False
        webhook_thread = threading.Thread(target=send_webhook)
        webhook_thread.start()

def send_webhook():
    global stop_webhook_thread
    while not stop_webhook_thread:
        screenshot_path = capture_screenshot()
        system_info = get_system_info()
        embed = {
            "title": f"Thông tin hệ thống - {device_name}",
            "color": 15258703,
            "fields": [
                {"name": "Tên thiết bị", "value": device_name, "inline": True},
                {"name": "CPU", "value": f"{system_info['cpu_usage']}%", "inline": True},
                {"name": "RAM đã dùng", "value": f"{system_info['memory_used'] / system_info['memory_total'] * 100:.2f}%", "inline": True},
                {"name": "RAM trống", "value": f"{system_info['memory_available'] / system_info['memory_total'] * 100:.2f}%", "inline": True},
                {"name": "Tổng RAM", "value": f"{system_info['memory_total'] / (1024 ** 3):.2f} GB", "inline": True},
                {"name": "Uptime", "value": f"{system_info['uptime'] / 3600:.2f} giờ", "inline": True}
            ],
            "image": {"url": "attachment://screenshot.png"}
        }
        payload = {"embeds": [embed], "username": device_name}
        with open(screenshot_path, "rb") as file:
            response = requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files={"file": ("screenshot.png", file)})
        if response.status_code in (200, 204):
            print(Fore.GREEN + "Webhook gửi thành công!" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Lỗi gửi webhook: {response.status_code}" + Style.RESET_ALL)
        time.sleep(interval * 60)

def stop_webhook():
    global stop_webhook_thread
    stop_webhook_thread = True

def setup_webhook():
    global webhook_url, device_name, interval, stop_webhook_thread
    stop_webhook_thread = True
    webhook_url = input(Fore.MAGENTA + "Nhập URL Webhook: " + Style.RESET_ALL)
    device_name = input(Fore.MAGENTA + "Nhập tên thiết bị: " + Style.RESET_ALL)
    interval = int(input(Fore.MAGENTA + "Nhập khoảng thời gian gửi webhook (phút): " + Style.RESET_ALL))
    save_config()
    stop_webhook_thread = False
    threading.Thread(target=send_webhook).start()

def kill_roblox_processes():
    print(Fore.YELLOW + "Đang tắt tất cả Roblox..." + Style.RESET_ALL)
    for package_name in get_roblox_packages():
        print(Fore.YELLOW + f"Đang tắt {package_name}..." + Style.RESET_ALL)
        os.system(f"pkill -f {package_name}")
    time.sleep(2)

def kill_roblox_process(package_name):
    print(Fore.GREEN + f"Đã tắt {package_name}." + Style.RESET_ALL)
    os.system(f"pkill -f {package_name}")
    time.sleep(2)

def launch_roblox(package_name, server_link, num_packages):
    try:
        subprocess.run(['am', 'start', '-n', f'{package_name}/com.roblox.client.startup.ActivitySplash', '-d', server_link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(Fore.GREEN + f"Đang mở {package_name}..." + Style.RESET_ALL)
        time.sleep(10)
        subprocess.run(['am', 'start', '-n', f'{package_name}/com.roblox.client.ActivityProtocolLaunch', '-d', server_link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(Fore.GREEN + f"Đã vào {package_name} với server: {server_link}" + Style.RESET_ALL)
        time.sleep(10)
        print_status_table(accounts)
    except Exception as e:
        print(Fore.RED + f"Lỗi mở {package_name}: {e}" + Style.RESET_ALL)

def format_server_link(input_link):
    if 'roblox.com' in input_link:
        return input_link
    elif input_link.isdigit():
        return f'roblox://placeID={input_link}'
    else:
        print(Fore.RED + "Liên kết không hợp lệ!" + Style.RESET_ALL)
        return None

def save_server_links(server_links):
    with open(SERVER_LINKS_FILE, "w") as file:
        for package, link in server_links:
            file.write(f"{package},{link}\n")

def load_server_links():
    server_links = []
    if os.path.exists(SERVER_LINKS_FILE):
        with open(SERVER_LINKS_FILE, "r") as file:
            for line in file:
                package, link = line.strip().split(",", 1)
                server_links.append((package, link))
    return server_links

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as file:
        for package, user_id in accounts:
            file.write(f"{package},{user_id}\n")

def load_accounts():
    accounts = []
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            for line in file:
                package, user_id = line.strip().split(",", 1)
                accounts.append((package, user_id))
    return accounts

def find_userid_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            userid_start = content.find('"UserId":"') + len('"UserId":"')
            if userid_start == -1:
                print(Fore.RED + "Không tìm thấy User ID." + Style.RESET_ALL)
                return None
            userid_end = content.find('"', userid_start)
            return content[userid_start:userid_end]
    except IOError as e:
        print(Fore.RED + f"Lỗi đọc file: {e}" + Style.RESET_ALL)
        return None

async def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {"usernames": [username], "excludeBannedUsers": True}
    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            return data['data'][0]['id'] if 'data' in data and data['data'] else None

def get_username(user_id):
    try:
        url = f"https://users.roblox.com/v1/users/{user_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json().get("name", "Không rõ")
    except Exception as e:
        print(Fore.RED + f"Lỗi lấy tên người dùng {user_id}: {e}" + Style.RESET_ALL)
        return None

def check_user_online(user_id):
    try:
        url = "https://presence.roblox.com/v1/presence/users"
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({"userIds": [user_id]})
        response = requests.post(url, headers=headers, data=body)
        response.raise_for_status()
        return response.json()["userPresences"][0]["userPresenceType"]
    except Exception as e:
        print(Fore.RED + f"Lỗi kiểm tra trạng thái {user_id}: {e}" + Style.RESET_ALL)
        return None

def print_menu():
    print_header()
    menu = (
        Fore.CYAN + "╔════════════════════ MENU CHÍNH ════════════════════╗\n" +
        "║ " + Fore.GREEN + "1. Bắt đầu Auto Rejoin cho Roblox Game" + Style.RESET_ALL + Fore.CYAN + "         ║\n" +
        "║ " + Fore.GREEN + "2. Cùng ID Game hoặc Liên kết Server Riêng" + Style.RESET_ALL + Fore.CYAN + "     ║\n" +
        "║ " + Fore.GREEN + "3. Liên kết Server Riêng hoặc ID Game khác" + Style.RESET_ALL + Fore.CYAN + "     ║\n" +
        "║ " + Fore.GREEN + "4. Xóa User ID và/hoặc Liên kết Server Riêng" + Style.RESET_ALL + Fore.CYAN + "   ║\n" +
        "║ " + Fore.GREEN + "5. Cài đặt Webhook" + Style.RESET_ALL + Fore.CYAN + "                            ║\n" +
        "║ " + Fore.GREEN + "6. Tự động thiết lập User ID" + Style.RESET_ALL + Fore.CYAN + "                  ║\n" +
        "║ " + Fore.GREEN + "7. Danh sách" + Style.RESET_ALL + Fore.CYAN + "                                  ║\n" +
        "║ " + Fore.GREEN + "8. Thoát" + Style.RESET_ALL + Fore.CYAN + "                                      ║\n" +
        "╚═════════════════════════════════════════════════════╝\n" + Style.RESET_ALL +
        Fore.MAGENTA + "Nhập lựa chọn (1-8): " + Style.RESET_ALL
    )
    return input(menu)

def main():
    global accounts
    print_header()
    device_hwid = get_device_hwid()
    notify_flask_server(device_hwid)
    load_config()
    previous_status = {}
    while True:
        choice = print_menu()
        if choice == "1":
            if webhook_url and device_name and interval:
                start_webhook_thread()
            server_links = load_server_links()
            accounts = load_accounts()
            if not accounts:
                print(Fore.RED + "Không tìm thấy User ID!" + Style.RESET_ALL)
                time.sleep(2)
                continue
            elif not server_links:
                print(Fore.RED + "Không tìm thấy Server Link!" + Style.RESET_ALL)
                time.sleep(2)
                continue
            force_rejoin_interval = int(input(Fore.MAGENTA + "Nhập thời gian buộc rejoin (phút): " + Style.RESET_ALL)) * 60
            kill_roblox_processes()
            print(Fore.YELLOW + "Chờ 5 giây để khởi động lại..." + Style.RESET_ALL)
            time.sleep(5)
            num_packages = len(server_links)
            for package_name, server_link in server_links:
                launch_roblox(package_name, server_link, num_packages)
            start_time = time.time()
            while True:
                for package_name, user_id in accounts:
                    if not user_id.isdigit():
                        print(Fore.GREEN + f"Đang lấy User ID cho {user_id}..." + Style.RESET_ALL)
                        user_id = asyncio.run(get_user_id(user_id))
                        if user_id is None:
                            user_id = input(Fore.MAGENTA + "Nhập User ID: " + Style.RESET_ALL)
                    username = get_username(user_id) or user_id
                    presence_type = check_user_online(user_id)
                    if presence_type == 2:
                        print(Fore.GREEN + f"{username} ({user_id}) đang chơi." + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f"{username} ({user_id}) offline, kiểm tra lại..." + Style.RESET_ALL)
                        for attempt in range(5):
                            presence_type = check_user_online(user_id)
                            if presence_type == 2:
                                print(Fore.GREEN + f"{username} ({user_id}) đang chơi." + Style.RESET_ALL)
                                break
                            print(Fore.RED + f"Thử {attempt + 1}/5: {username} vẫn offline..." + Style.RESET_ALL)
                            time.sleep(3)
                        if presence_type != 2:
                            print(Fore.RED + f"{username} offline. Rejoining..." + Style.RESET_ALL)
                            kill_roblox_process(package_name)
                            launch_roblox(package_name, server_link, num_packages)
                    time.sleep(10)
                time.sleep(60)
                if time.time() - start_time >= force_rejoin_interval:
                    print(Fore.YELLOW + "Buộc thoát Roblox do hết thời gian..." + Style.RESET_ALL)
                    kill_roblox_processes()
                    start_time = time.time()
                    time.sleep(5)
                    for package_name, server_link in server_links:
                        launch_roblox(package_name, server_link, num_packages)
                previous_status = print_status_table(accounts, previous_status)
        elif choice == "2":
            server_link = input(Fore.MAGENTA + "Nhập ID Game/Server Link: " + Style.RESET_ALL)
            formatted_link = format_server_link(server_link)
            if formatted_link:
                packages = get_roblox_packages()
                server_links = [(package_name, formatted_link) for package_name in packages]
                save_server_links(server_links)
                print(Fore.GREEN + "Đã lưu Server Link!" + Style.RESET_ALL)
                time.sleep(2)
        elif choice == "3":
            packages = get_roblox_packages()
            server_links = []
            for package_name in packages:
                server_link = input(Fore.YELLOW + f"Nhập ID Game/Server Link cho {package_name}: " + Style.RESET_ALL)
                formatted_link = format_server_link(server_link)
                if formatted_link:
                    server_links.append((package_name, formatted_link))
            save_server_links(server_links)
            print(Fore.GREEN + "Đã lưu Server Link riêng!" + Style.RESET_ALL)
            time.sleep(2)
        elif choice == "4":
            print(Fore.CYAN + "╔═════ XÓA DỮ LIỆU ═════╗\n" +
                  "║ 1. Xóa User ID        ║\n" +
                  "║ 2. Xóa Server Link    ║\n" +
                  "║ 3. Xóa cả hai         ║\n" +
                  "╚═══════════════════════╝" + Style.RESET_ALL)
            clear_choice = input(Fore.MAGENTA + "Chọn (1-3): " + Style.RESET_ALL)
            if clear_choice == "1" and os.path.exists(ACCOUNTS_FILE):
                os.remove(ACCOUNTS_FILE)
                print(Fore.GREEN + "Đã xóa User ID!" + Style.RESET_ALL)
            elif clear_choice == "2" and os.path.exists(SERVER_LINKS_FILE):
                os.remove(SERVER_LINKS_FILE)
                print(Fore.GREEN + "Đã xóa Server Link!" + Style.RESET_ALL)
            elif clear_choice == "3":
                if os.path.exists(ACCOUNTS_FILE):
                    os.remove(ACCOUNTS_FILE)
                if os.path.exists(SERVER_LINKS_FILE):
                    os.remove(SERVER_LINKS_FILE)
                print(Fore.GREEN + "Đã xóa cả User ID và Server Link!" + Style.RESET_ALL)
            time.sleep(2)
        elif choice == "5":
            setup_webhook()
        elif choice == "6":
            print(Fore.GREEN + "Tự động cài User ID từ appStorage..." + Style.RESET_ALL)
            packages = get_roblox_packages()
            accounts = []
            for package_name in packages:
                file_path = f'/data/data/{package_name}/files/appData/LocalStorage/appStorage.json'
                user_id = find_userid_from_file(file_path)
                if user_id:
                    accounts.append((package_name, user_id))
                    print(Fore.GREEN + f"Tìm thấy User ID cho {package_name}: {user_id}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + f"Không tìm thấy User ID cho {package_name}." + Style.RESET_ALL)
            save_accounts(accounts)
            print(Fore.GREEN + "Đã lưu User ID từ appStorage!" + Style.RESET_ALL)
            server_link = input(Fore.YELLOW + "Nhập ID Game/Server Link: " + Style.RESET_ALL)
            formatted_link = format_server_link(server_link)
            if formatted_link:
                server_links = [(package_name, formatted_link) for package_name in packages]
                save_server_links(server_links)
                print(Fore.GREEN + "Đã lưu Server Link!" + Style.RESET_ALL)
            time.sleep(2)
        elif choice == "7":
            accounts = load_accounts()
            server_links = load_server_links()
            if not accounts or not server_links:
                print(Fore.RED + "Không tìm thấy tài khoản hoặc server link để hiển thị!" + Style.RESET_ALL)
                time.sleep(2)
                continue
            print_account_list(accounts, server_links)
        elif choice == "8":
            stop_webhook()
            print(Fore.GREEN + "Đã thoát Quy Bel Tool!" + Style.RESET_ALL)
            time.sleep(2)
            break
        else:
            print(Fore.RED + "Lựa chọn không hợp lệ!" + Style.RESET_ALL)
            time.sleep(2)

if __name__ == "__main__":
    main()