from flask import Flask, render_template, request
import pandas as pd
import datetime

app = Flask(__name__)

# Google Sheets 설정
STUDENT_SHEET_URL = 'https://docs.google.com/spreadsheets/d/11RqrhH7lIUnCmOFM0RPZeqcMHT_OVGiFjMzfByJQCJw/export?format=csv'
TIMETABLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fydu0QvrnIMI3qAwKYh5vcD42b-slxa2QBnJx-8h9uo/export?format=csv'

def get_sheet_data(url):
    try:
        return pd.read_csv(url, error_bad_lines=False, warn_bad_lines=True)
    except pd.errors.ParserError as e:
        print("Error reading CSV:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subject', methods=['POST'])
def get_subject():
    grade = request.form['grade']
    class_number = request.form['class_number']
    student_data = get_sheet_data(STUDENT_SHEET_URL)
    timetable_data = get_sheet_data(TIMETABLE_SHEET_URL)

    if student_data is None or timetable_data is None:
        return 'Error reading Google Sheets data.'

    current_subject = find_current_subject(grade, class_number, timetable_data)

    return render_template('subject.html', subject=current_subject)

def find_current_subject(grade, class_number, timetable_data):
    now = datetime.datetime.now()
    current_day = now.weekday()  # 월요일=0, 일요일=6
    current_time = now.time()

    # 교시별 시간대 설정
    periods = [
        (datetime.time(8, 30), datetime.time(9, 20)),
        (datetime.time(9, 30), datetime.time(10, 20)),
        (datetime.time(10, 30), datetime.time(11, 20)),
        (datetime.time(11, 30), datetime.time(12, 20)),
        (datetime.time(13, 20), datetime.time(14, 10)),
        (datetime.time(14, 20), datetime.time(15, 10)),
        (datetime.time(15, 20), datetime.time(16, 10))
    ]

    # 현재 교시 찾기
    period_index = -1
    for i, (start, end) in enumerate(periods):
        if start <= current_time <= end:
            period_index = i
            break

    # 쉬는 시간일 경우 다음 교시로 변경
    if period_index == -1:
        for i, (start, end) in enumerate(periods):
            if current_time < start:
                period_index = i
                break

    # 현재 교시가 마지막 교시 이후인 경우
    if period_index == -1 or period_index >= len(periods):
        return "No class at this time"

    # 현재 요일의 시간표 정보 가져오기
    try:
        grade_class_column = f"{grade}-{class_number}"
        if current_day < len(timetable_data.columns) - 1:
            current_subject = timetable_data.iloc[period_index][grade_class_column]
        else:
            return "No class at this time"
    except (IndexError, KeyError):
        return "No data for the specified grade and class"

    return current_subject

if __name__ == '__main__':
    app.run(debug=True)
