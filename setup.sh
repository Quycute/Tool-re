pkg install curl && curl -sL -H "Cache-Control: no-cache" <<'EOF' | bash
#!/data/data/com.termux/files/usr/bin/bash

# Cập nhật Termux và cài các gói cần thiết
pkg update && pkg upgrade
pkg install python
pip install requests aiohttp psutil colorama

# Tải quybeltool.py
curl -L -o quybeltool.py "https://raw.githubusercontent.com/Quycute/Tool-re/refs/heads/main/quybeltool.py"

echo "Cài đặt hoàn tất! Chạy tool bằng: python quybeltool.py"
EOF
