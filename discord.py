import requests

def send_message(message):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1345365931186196510/Gk9d1Nv-c03szRIdpqdRbvyHWVxu0JwI1QTsvUDTwWTciHmidBEMYos5Ua5JOxPZvOK4"  # 여기에 복사한 웹훅 URL 입력

    for symbol, signal in message.items():
        data = {
            "content": f"> {symbol}\n{signal}"
        }

        response = requests.post(WEBHOOK_URL, json=data)

        if response.status_code == 204:
            print("✅ 메시지 전송 성공!")
        else:
            print(f"❌ 전송 실패: {response.status_code}, {response.text}")
