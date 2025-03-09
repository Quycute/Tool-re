pkg install curl && curl -sL -H "Cache-Control: no-cache" <<'EOF' | bash
#!/data/data/com.termux/files/usr/bin/bash

# Màu sắc cho giao diện
RED='\e[31m'
GREEN='\e[32m'
YELLOW='\e[33m'
CYAN='\e[36m'
RESET='\e[0m'

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
pkg update && pkg upgrade
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Lỗi khi cập nhật Termux. Vui lòng kiểm tra kết nối mạng!${RESET}"
    exit 1
fi

# Cài đặt Python
echo -e "${GREEN}[*] Cài đặt Python...${RESET}"
pkg install python
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

# Tải file quybeltool.py
echo -e "${GREEN}[*] Tải quybeltool.py...${RESET}"
curl -L -o quybeltool.py "https://raw.githubusercontent.com/Quycute/Tool-re/refs/heads/main/quybeltool.py"
if [ $? -ne 0 ]; then
    echo -e "${RED}[!] Lỗi khi tải quybeltool.py!${RESET}"
    exit 1
fi

# Hoàn tất cài đặt
echo -e "${CYAN}╔════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║       Cài đặt hoàn tất!           ║${RESET}"
echo -e "${CYAN}╚════════════════════════════════════╝${RESET}"
echo -e "${YELLOW}Để chạy tool, gõ: python quybeltool.py${RESET}"
EOF
