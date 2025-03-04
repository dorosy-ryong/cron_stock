import requests
import pandas as pd

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

def send_message_table(message):
    WEBHOOK_URL = "https://discord.com/api/webhooks/1345365931186196510/Gk9d1Nv-c03szRIdpqdRbvyHWVxu0JwI1QTsvUDTwWTciHmidBEMYos5Ua5JOxPZvOK4"  # 여기에 복사한 웹훅 URL 입력

    result = []
    for stock_name, df in message.items():
        last_3_days = df.tail(3)
        bs_2d = last_3_days['buy_signal_rate'].iloc[0]  # 2일 전
        bs_1d = last_3_days['buy_signal_rate'].iloc[1]  # 1일 전
        bs_today = last_3_days['buy_signal_rate'].iloc[2]  # 오늘
        ss_2d = last_3_days['sell_signal_rate'].iloc[0]  # 2일 전
        ss_1d = last_3_days['sell_signal_rate'].iloc[1]  # 1일 전
        ss_today = last_3_days['sell_signal_rate'].iloc[2]  # 오늘
        
        # 종목과 해당 Close 값을 하나의 행으로 추가
        result.append([stock_name, bs_today, ss_today, bs_1d, ss_1d, bs_2d, ss_2d])

    # 결과를 DataFrame으로 변환
    final_df = pd.DataFrame(result, columns=['종목', 'bs_today', 'ss_today', 'bs_1d', 'ss_1d', 'bs_2d', 'ss_2d'])

    # Markdown 형식으로 테이블 생성
    # 수동으로 Markdown 형식의 테이블 생성
    markdown_table = "종목 | Buy Signal Today | Sell Signal Today | Buy Signal 1일전 | Sell Signal 1일전 | Buy Signal 2일전 | Sell Signal 2일전\n"
    markdown_table += "---|-------------|-------------|------------|-----------|-------------|------------\n"

    for row in final_df.values:
        markdown_table += " | ".join(map(str, row)) + "\n"

    print(markdown_table)

    response = requests.post(WEBHOOK_URL, json={'content': "```markdown\n" + markdown_table + "```"})

    if response.status_code == 204:
        print("✅ 메시지 전송 성공!")
    else:
        print(f"❌ 전송 실패: {response.status_code}, {response.text}")
