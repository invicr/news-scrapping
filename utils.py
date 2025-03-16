from datetime import datetime


def get_current_month_and_week():
    today = datetime.today()  # 현재 날짜와 시간을 가져옴
    # 현재 월
    current_month = today.month
    # 현재 날짜가 그 달의 몇 번째 주에 해당하는지 계산
    current_week = (today.day - 1) // 7 + 1
    return current_month, current_week
