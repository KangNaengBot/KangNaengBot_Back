import qrcode

# QR코드로 만들 URL
url = "https://gangnangbot.vercel.app/login"

# QR 코드 생성 설정
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

qr.add_data(url)
qr.make(fit=True)

# 이미지 생성 및 저장
img = qr.make_image(fill_color="black", back_color="white")
output_file = "kangnangbot_notion_qr.png"
img.save(output_file)

print(f"✅ QR 코드가 생성되었습니다: {output_file}")
