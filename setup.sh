#!/data/data/com.termux/files/usr/bin/bash

# Màu sắc cho giao diện
RED='\e[31m'
GREEN='\e[32m'
YELLOW='\e[33m'
CYAN='\e[36m'
RESET='\e[0m'

# URL của file quybeltool.py
PYTHON_URL="https://raw.githubusercontent.com/Quycute/Tool-re/refs/heads/main/quybeltool.py"

# Đường dẫn thư mục Download
DOWNLOAD_DIR="$HOME/storage/downloads"

# Hiển thị tiêu đề
clear
echo -e "${CYAN}╔════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║       Quy Bel Tool Setup          ║${RESET}"
echo -e "${CYAN}║   Auto Rejoin Roblox - Termux     ║${RESET}"
echo -e "${CYAN}╚════════════════════════════════════╝${RESET}"
echo -e "${YELLOW}Bắt đầu cài đặt tool...${RESET}"
sleep 2

# Cập nhật Termux và cài đặt gói cơ bản
echo -e "${GREEN}[*] Cập nhật Termux...${RESET}"
pkg update -y && pkg upgrade -y
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Lỗi khi cập nhật Termux. Vui lòng kiểm tra kết nối mạng!${RESET}"
    exit 1
fi

# Cài đặt Python
echo -e "${GREEN}[*] Cài đặt Python...${RESET}"
pkg install python -y
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Lỗi khi cài đặt Python!${RESET}"
    exit 1
fi

# Cài đặt các thư viện Python cần thiết
echo -e "${GREEN}[*] Cài đặt các thư viện Python...${RESET}"
pip install requests aiohttp psutil colorama
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Lỗi khi cài đặt thư viện Python!${RESET}"
    exit 1
fi

# Thiết lập quyền truy cập bộ nhớ để dùng thư mục Download
echo -e "${GREEN}[*] Thiết lập quyền truy cập bộ nhớ...${RESET}"
termux-setup-storage
if [ ! -d "$DOWNLOAD_DIR" ]; then
    echo -e "${RED}[!] Không tìm thấy thư mục Download. Đảm bảo đã cấp quyền truy cập bộ nhớ!${RESET}"
    exit 1
fi

# Di chuyển vào thư mục Download
cd "$DOWNLOAD_DIR" || exit 1

# Tải file quybeltool.py từ URL
echo -e "${GREEN}[*] Tải quybeltool.py từ $PYTHON_URL...${RESET}"
curl -L -o quybeltool.py "$PYTHON_URL"
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Lỗi khi tải file quybeltool.py!${RESET}"
    echo -e "${YELLOW}Vui lòng kiểm tra kết nối mạng hoặc URL và thử lại.${RESET}"
    exit 1
fi

# Cấp quyền thực thi cho file
chmod +x quybeltool.py
echo -e "${GREEN}[*] Đã cấp quyền thực thi cho quybeltool.py${RESET}"

# Tạo alias để chạy tool dễ dàng
echo -e "${GREEN}[*] Tạo alias để chạy tool...${RESET}"
echo "alias quybeltool='python $DOWNLOAD_DIR/quybeltool.py'" >> "$HOME/.bashrc"
source "$HOME/.bashrc"
echo -e "${GREEN}[*] Đã thêm alias 'quybeltool'. Gõ 'quybeltool' để chạy từ bất kỳ đâu.${RESET}"

# Hoàn tất cài đặt
echo -e "${CYAN}╔════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║       Cài đặt hoàn tất!           ║${RESET}"
echo -e "${CYAN}╚════════════════════════════════════╝${RESET}"
echo -e "${GREEN}[*] Tool đã được lưu tại: $DOWNLOAD_DIR/quybeltool.py${RESET}"
echo -e "${GREEN}[*] Để chạy tool, di chuyển đến $DOWNLOAD_DIR và gõ:${RESET}"
echo -e "${YELLOW}    python quybeltool.py${RESET}"
echo -e "${GREEN}[*] Hoặc gõ 'quybeltool' từ bất kỳ đâu.${RESET}"