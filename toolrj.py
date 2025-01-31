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

bypass_status = "Chưa sử dụng"

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    header = (
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⣴⣶⣶⣶⣶⣶⠶⣶⣤⣤⣀⠀⠀⠀⠀⠀⠀ \n"
        "⠀⠀⠀⠀⠀⠀⠀⢀⣤⣾⣿⣿⣿⠁⠀⢀⠈⢿⢀⣀⠀⠹⣿⣿⣿⣦⣄⠀⠀⠀ \n"
        "⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⠿⠀⠀⣟⡇⢘⣾⣽⠀⠀⡏⠉⠙⢛⣿⣷⡖⠀ \n"
        "⠀⠀⠀⠀⠀⣾⣿⣿⡿⠿⠷⠶⠤⠙⠒⠀⠒⢻⣿⣿⡷⠋⠀⠴⠞⠋⠁⢙⣿⣄ \n"
        "⠀⠀⠀⠀⢸⣿⣿⣯⣤⣤⣤⣤⣤⡄⠀⠀⠀⠀⠉⢹⡄⠀⠀⠀⠛⠛⠋⠉⠹⡇ \n"
        "⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀⣀⣠⣤⣤⣤⣤⣤⣤⣤⣼⣇⣀⣀⣀⣛⣛⣒⣲⢾⡷ \n"
        "⢀⠤⠒⠒⢼⣿⣿⠶⠞⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠁⠀⣼⠃ \n"
        "⢮⠀⠀⠀⠀⣿⣿⣆⠀⠀⠻⣿⡿⠛⠉⠉⠁⠀⠉⠉⠛⠿⣿⣿⠟⠁⠀⣼⠃⠀ \n"
        "⠈⠓⠶⣶⣾⣿⣿⣿⣧⡀⠀⠈⠒⢤⣀⣀⡀⠀⠀⣀⣀⡠⠚⠁⠀⢀⡼⠃⠀⠀ \n"
        "⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣷⣤⣤⣤⣤⣭⣭⣭⣭⣭⣥⣤⣤⣤⣴⣟⠁ \n"
                                           "xin chao den quy bel tool \n"

 )
   
    print(header)

print_header()

def print_status_table(bypass_status, accounts, previous_status=None):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(
        "------------------- Bảng Trạng Thái -------------------\n"
        "| Roblox Game Rejoin          |  Đang hoạt động         |\n"
        f"| Fluxus Bypass              |  {bypass_status}        |\n"
        "------------------------------------------------------"
    )
    if previous_status is None:
        previous_status = {}
    for package_name, user_id in accounts:
        username = get_username(user_id) or user_id
        status = check_user_online(user_id)
        if status == 2:
            status_text = "Đang chơi"
        elif status == 1:
            status_text = "Đang chờ trong sảnh"
        else:
            status_text = "Offline"
        if previous_status.get(user_id) != status_text:
            print(f"| {package_name} | {username} | {status_text} |")
            previous_status[user_id] = status_text
    print("------------------------------------------------------")
    return previous_status

def get_device_hwid():
    hwid = str(uuid.uuid1())
    hwid_hash = hashlib.sha256(hwid.encode()).hexdigest()
    return hwid_hash

def notify_flask_server(hwid):
    data = {"hwid": hwid}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(FLASK_SERVER_URL, json=data, headers=headers)
    except Exception as e:
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
    system_info = {
        "cpu_usage": cpu_usage,
        "memory_total": memory_info.total,
        "memory_available": memory_info.available,
        "memory_used": memory_info.used,
        "uptime": uptime
    }
    return system_info

def load_config():
    global webhook_url, device_name, interval
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            webhook_url = config.get("webhook_url")
            device_name = config.get("device_name")
            interval = config.get("interval")
    else:
        webhook_url = None
        device_name = None
        interval = None

def save_config():
    config = {
        "webhook_url": webhook_url,
        "device_name": device_name,
        "interval": interval
    }
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
            "title": f"Thông tin hệ thống của {device_name}",
            "color": 15258703,
            "fields": [
                {"name": "Tên thiết bị", "value": device_name, "inline": True},
                {"name": "Sử dụng CPU", "value": f"{system_info['cpu_usage']}%", "inline": True},
                {"name": "Bộ nhớ đã dùng", "value": f"{system_info['memory_used'] / system_info['memory_total'] * 100:.2f}%", "inline": True},
                {"name": "Bộ nhớ trống", "value": f"{system_info['memory_available'] / system_info['memory_total'] * 100:.2f}%", "inline": True},
                {"name": "Tổng dung lượng bộ nhớ", "value": f"{system_info['memory_total'] / (1024 ** 3):.2f} GB", "inline": True},
                {"name": "Thời gian hoạt động", "value": f"{system_info['uptime'] / 3600:.2f} giờ", "inline": True}
            ],
            "image": {"url": "attachment://screenshot.png"}
        }
        payload = {
            "embeds": [embed],
            "username": device_name
        }
        with open(screenshot_path, "rb") as file:
            response = requests.post(
                webhook_url,
                data={"payload_json": json.dumps(payload)},
                files={"file": ("screenshot.png", file)}
            )
        if response.status_code == 204 or response.status_code == 200:
            print(Fore.GREEN + "Thông tin thiết bị đã được gửi đến webhook thành công." + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Lỗi gửi thông tin thiết bị đến webhook, mã trạng thái: {response.status_code}" + Style.RESET_ALL)
        time.sleep(interval * 60)

def stop_webhook():
    global stop_webhook_thread
    stop_webhook_thread = True

def setup_webhook():
    global webhook_url, device_name, interval, stop_webhook_thread
    stop_webhook_thread = True
    webhook_url = input(Fore.MAGENTA + "Vui lòng nhập URL Webhook của bạn: " + Style.RESET_ALL)
    device_name = input(Fore.MAGENTA + "Vui lòng nhập tên thiết bị của bạn: " + Style.RESET_ALL)
    interval = int(input(Fore.MAGENTA + "Vui lòng nhập khoảng thời gian để gửi thông tin thiết bị đến Webhook (tính bằng phút): " + Style.RESET_ALL))
    save_config()
    stop_webhook_thread = False
    threading.Thread(target=send_webhook).start()

def kill_roblox_processes():
    print(Fore.YELLOW + "Đang tắt tất cả các trò chơi Roblox trên thiết bị của bạn..." + Style.RESET_ALL)
    package_names = get_roblox_packages()
    for package_name in package_names:
        print(Fore.YELLOW + f"Đang tắt trò chơi Roblox: {package_name}" + Style.RESET_ALL)
        os.system(f"pkill -f {package_name}")
    time.sleep(2)

def kill_roblox_process(package_name):
    print(Fore.GREEN + f"Trò chơi Roblox {package_name} đã bị tắt." + Style.RESET_ALL)
    os.system(f"pkill -f {package_name}")
    time.sleep(2)

def launch_roblox(package_name, server_link, num_packages):
    try:
        subprocess.run(['am', 'start', '-n', f'{package_name}/com.roblox.client.startup.ActivitySplash', '-d', server_link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(Fore.GREEN + f"Đang mở Roblox cho {package_name}..." + Style.RESET_ALL)

        time.sleep(10)

        subprocess.run(['am', 'start', '-n', f'{package_name}/com.roblox.client.ActivityProtocolLaunch', '-d', server_link], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(Fore.GREEN + f"Đã vào Roblox cho {package_name} với liên kết server: {server_link}." + Style.RESET_ALL)

        time.sleep(10)

        os.system('cls' if os.name == 'nt' else 'clear')  # Xóa màn hình và hiển thị bảng trạng thái sau khi Roblox đã khởi động
        print_status_table(bypass_status, accounts)

    except Exception as e:
        print(Fore.RED + f"Lỗi khi mở Roblox cho {package_name}: {e}" + Style.RESET_ALL)

def format_server_link(input_link):
    if 'roblox.com' in input_link:
        return input_link
    elif input_link.isdigit():
        return f'roblox://placeID={input_link}'
    else:
        print(Fore.RED + "Liên kết không hợp lệ! Vui lòng nhập ID trò chơi hoặc liên kết server riêng tư hợp lệ." + Style.RESET_ALL)
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
            userid_start = content.find('"UserId":"')
            if userid_start == -1:
                print(Fore.RED + "Không tìm thấy User ID." + Style.RESET_ALL)
                return None
            userid_start += len('"UserId":"')
            userid_end = content.find('"', userid_start)
            if userid_end == -1:
                print("Không tìm thấy kết thúc của User ID.")
                return None
            userid = content[userid_start:userid_end]
            return userid
    except IOError as e:
        print(Fore.RED + f"Lỗi khi đọc file: {e}" + Style.RESET_ALL)
        return None

async def get_user_id(username):
    url = "https://users.roblox.com/v1/usernames/users"
    payload = {
        "usernames": [username],
        "excludeBannedUsers": True
    }
    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            data = await response.json()
            if 'data' in data and len(data['data']) > 0:
                return data['data'][0]['id']
    return None

def get_username(user_id):
    try:
        url = f"https://users.roblox.com/v1/users/{user_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("name", "Không rõ")
    except Exception as e:
        print(Fore.RED + f"Lỗi lấy tên người dùng cho User ID {user_id}: {e}" + Style.RESET_ALL)
        return None

def check_user_online(user_id):
    try:
        url = "https://presence.roblox.com/v1/presence/users"
        headers = {'Content-Type': 'application/json'}
        body = json.dumps({"userIds": [user_id]})
        response = requests.post(url, headers=headers, data=body)
        response.raise_for_status()
        data = response.json()
        presence_type = data["userPresences"][0]["userPresenceType"]
        return presence_type
    except Exception as e:
        print(Fore.RED + f"Lỗi kiểm tra trạng thái online, mã trạng thái: {e}" + Style.RESET_ALL)
        return None

def create_bypass_link(hwid_link, api_key="toolkey"):
    return f"http://103.65.235.193:8264/api/fluxus?hwid_link={hwid_link}&api_key={api_key}"

def bypass_fluxus(accounts):
    bypassed_results = []
    global bypass_status
    bypass_status = "Đang sử dụng"
    for package_name, user_id in accounts:
        fluxus_hwid_path = f"/data/data/{package_name}/app_assets/content/"
        files = os.listdir(fluxus_hwid_path)
        hwid_file = files[0] if files else None
        if hwid_file:
            with open(os.path.join(fluxus_hwid_path, hwid_file), 'r') as file:
                hwid = file.read().strip()
            hwid_link = f"https://flux.li/android/external/start.php?HWID={hwid}"
            bypass_link = create_bypass_link(hwid_link)
            username = get_username(user_id) or user_id
            try:
                response = requests.get(bypass_link)
                if response.status_code == 200:
                    bypassed_results.append((package_name, response.json()))
                    print(Fore.GREEN + f"{username}: Fluxus bypass thành công - {response.json()}" + Style.RESET_ALL)
                else:
                    print(Fore.RED + f"{username}: Fluxus bypass thất bại, mã trạng thái: {response.status_code}" + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"{username}: Lỗi Fluxus bypass: {str(e)}" + Style.RESET_ALL)
    return bypassed_results

def main():
    print_header()
    device_hwid = get_device_hwid()
    notify_flask_server(device_hwid)
    load_config()
    previous_status = {}
    while True:
        setup_type = input(Fore.CYAN + "Vui lòng chọn chức năng:\n1. Bắt đầu Auto Rejoin cho Roblox Game\n2. Cài đặt User ID cho mỗi Gói\n3. Cùng ID Game hoặc Liên kết Server Riêng\n4. same id game và svv (nên sử dụng thay chức năng 3)\n5. Xóa User ID và/hoặc Liên kết Server Riêng " + Style.RESET_ALL)
        if setup_type == "1":
            if webhook_url and device_name and interval:
                webhook_thread = threading.Thread(target=send_webhook)
                webhook_thread.start()
            server_links = load_server_links()
            accounts = load_accounts()
            if not accounts:
                print(Fore.RED + "Không tìm thấy User ID, vui lòng thử lại sau." + Style.RESET_ALL)
                continue
            elif not server_links:
                print(Fore.RED + "Không tìm thấy ID Game hoặc Liên kết Server Riêng, vui lòng thử lại sau." + Style.RESET_ALL)
                continue
            force_rejoin_interval = int(input(Fore.MAGENTA + "Nhập thời gian bắt buộc khởi động lại Roblox game (tính bằng phút): " + Style.RESET_ALL)) * 60
            print(Fore.YELLOW + "Đang tắt các trò chơi Roblox..." + Style.RESET_ALL)
            kill_roblox_processes()
            print(Fore.YELLOW + "Chờ 5 giây để khởi động lại Roblox..." + Style.RESET_ALL)
            time.sleep(5)
            num_packages = len(server_links)
            for package_name, server_link in server_links:
                launch_roblox(package_name, server_link, num_packages)
            start_time = time.time()
            while True:
                for package_name, user_id in accounts:
                    if not user_id.isdigit():
                        print(Fore.GREEN + f"Đang lấy User ID cho tên người dùng: {user_id}..." + Style.RESET_ALL)
                        user_id = asyncio.run(get_user_id(user_id))
                        if user_id is None:
                            print(Fore.RED + "Lỗi khi lấy User ID, vui lòng thử lại sau." + Style.RESET_ALL)
                            user_id = input(Fore.MAGENTA + "Nhập User ID của bạn: " + Style.RESET_ALL)
                    username = get_username(user_id) or user_id
                    presence_type = check_user_online(user_id)
                    if presence_type == 2:
                        print(Fore.GREEN + f"{username} ({user_id}) vẫn đang chơi trong game." + Style.RESET_ALL)
                    else:
                        print(Fore.RED + f"{username} ({user_id}) đã offline hoặc ở trạng thái khác. Kiểm tra lại..." + Style.RESET_ALL)
                        max_retries = 5
                        retry_interval = 3
                        for attempt in range(max_retries):
                            presence_type = check_user_online(user_id)
                            if presence_type == 2:
                                print(Fore.GREEN + f"{username} ({user_id}) vẫn đang chơi trong game." + Style.RESET_ALL)
                                break
                            else:
                                print(Fore.RED + f"Thử lại {attempt + 1}/{max_retries}: {username} ({user_id}) vẫn offline. Chờ {retry_interval} giây để thử lại..." + Style.RESET_ALL)
                                time.sleep(retry_interval)
                        if presence_type != 2:
                            print(Fore.RED + f"{username} ({user_id}) đã offline. Đang rejoin..." + Style.RESET_ALL)
                            kill_roblox_process(package_name)
                            launch_roblox(package_name, server_link, num_packages)
                    time.sleep(5)
                time.sleep(60)
                if time.time() - start_time >= force_rejoin_interval:
                    print("Bắt buộc thoát tiến trình Roblox do quá thời gian.")
                    kill_roblox_processes()
                    start_time = time.time()
                    print(Fore.YELLOW + "Chờ 5 giây để khởi động lại Roblox..." + Style.RESET_ALL)
                    time.sleep(5)
                    for package_name, server_link in server_links:
                        launch_roblox(package_name, server_link, num_packages)
                previous_status = print_status_table(bypass_status, accounts, previous_status)
        elif setup_type == "2":
            accounts = []
            packages = get_roblox_packages()
            for package_name in packages:
                user_input = input(Fore.MAGENTA + f"Nhập ID Game hoặc Liên kết Server Riêng cho {package_name}: " + Style.RESET_ALL)
                user_id = None
                if user_input.isdigit():
                    user_id = user_input
                else:
                    print(Fore.GREEN + f"Đang lấy User ID cho tên người dùng: {user_input}..." + Style.RESET_ALL)
                    user_id = asyncio.run(get_user_id(user_input))
                    if user_id is None:
                        print(Fore.RED + "Không lấy được User ID. Vui lòng nhập User ID thủ công." + Style.RESET_ALL)
                        user_id = input(Fore.MAGENTA + "Nhập User ID của bạn: " + Style.RESET_ALL)
                accounts.append((package_name, user_id))
                print(Fore.GREEN + f"Đã cài đặt {package_name} cho User ID: {user_id}" + Style.RESET_ALL)
            save_accounts(accounts)
            print(Fore.GREEN + "Đã lưu User ID." + Style.RESET_ALL)
        elif setup_type == "3":
            server_link = input(Fore.MAGENTA + "Nhập ID Game hoặc Liên kết Server Riêng của bạn: " + Style.RESET_ALL)
            formatted_link = format_server_link(server_link)
            if formatted_link:
                packages = get_roblox_packages()
                server_links = [(package_name, formatted_link) for package_name in packages]
                save_server_links(server_links)
                print(Fore.GREEN + "Đã lưu ID Game hoặc Liên kết Server Riêng thành công!" + Style.RESET_ALL)
        elif setup_type == "4":
            packages = get_roblox_packages()
            server_links = []
            for package_name in packages:
                server_link = input(Fore.YELLOW + f"Nhập ID Game hoặc Liên kết Server Riêng cho {package_name}: " + Style.RESET_ALL)
                formatted_link = format_server_link(server_link)
                if formatted_link:
                    server_links.append((package_name, formatted_link))
            save_server_links(server_links)
        elif setup_type == "5":
            clear_choice = input(Fore.GREEN + "Bạn có chắc chắn muốn xóa User ID hoặc Liên kết Server Riêng?\n1. Xóa User ID\n2. Xóa Liên kết Server Riêng\n3. Xóa cả User ID và Liên kết Server Riêng\nNhập lựa chọn: " + Style.RESET_ALL)
            if clear_choice == "1":
                os.remove(ACCOUNTS_FILE)
                print(Fore.GREEN + "Đã xóa User ID." + Style.RESET_ALL)
            elif clear_choice == "2":
                os.remove(SERVER_LINKS_FILE)
                print(Fore.GREEN + "Đã xóa Liên kết Server Riêng." + Style.RESET_ALL)
            elif clear_choice == "3":
                os.remove(ACCOUNTS_FILE)
                os.remove(SERVER_LINKS_FILE)
                print(Fore.GREEN + "Đã xóa User ID và Liên kết Server Riêng." + Style.RESET_ALL)
        elif setup_type == "6":
            setup_webhook()
        elif setup_type == "4":
            print(Fore.GREEN + "Tự động cài đặt User ID bằng appStorage.json..." + Style.RESET_ALL)
            packages = get_roblox_packages()
            accounts = []
            for package_name in packages:
                file_path = f'/data/data/{package_name}/files/appData/LocalStorage/appStorage.json'
                user_id = find_userid_from_file(file_path)
                if user_id:
                    accounts.append((package_name, user_id))
                    print(f"Tìm thấy User ID cho {package_name}: {user_id}")
                else:
                    print(Fore.RED + f"Không tìm thấy User ID cho {package_name}. Vui lòng thử lại sau." + Style.RESET_ALL)
            save_accounts(accounts)
            print(Fore.GREEN + "Đã lưu User ID từ appStorage.json." + Style.RESET_ALL)
            server_link = input(Fore.YELLOW + "Nhập ID Game hoặc Liên kết Server Riêng: " + Style.RESET_ALL)
            formatted_link = format_server_link(server_link)
            if formatted_link:
                server_links = [(package_name, formatted_link) for package_name in packages]
                save_server_links(server_links)
                print(Fore.GREEN + "Đã lưu ID Game và Liên kết Server Riêng thành công!" + Style.RESET_ALL)
        elif setup_type == "8":
            accounts = load_accounts()
            server_links = load_server_links()
            print(Fore.CYAN + "Danh sách Tên người dùng, User ID, Tên gói và Liên kết Server Riêng:" + Style.RESET_ALL)
            for (package_name, user_id), (_, server_link) in zip(accounts, server_links):
                username = get_username(user_id) or user_id
                print(Fore.CYAN + f"Tên gói: {package_name}, Tên người dùng: {username}, User ID: {user_id}, Liên kết Server Riêng: {server_link}" + Style.RESET_ALL)
        elif setup_type == "9":
            global stop_webhook_thread
            stop_webhook_thread = True
            break

if __name__ == "__main__":
    main()
