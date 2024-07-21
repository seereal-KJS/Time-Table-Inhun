from flask import Flask, render_template, request
import pandas as pd
import datetime

app = Flask(__name__)

# Google Sheets 설정
STUDENT_SHEET_URL = 'https://docs.google.com/spreadsheets/d/11RqrhH7lIUnCmOFM0RPZeqcMHT_OVGiFjMzfByJQCJw/export?format=csv'
TIMETABLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fydu0QvrnIMI3qAwKYh5vcD42b-slxa2QBnJx-8h9uo/export?format=csv'

def get_sheet_data(url):
    try:
        return pd.read_csv(url, on_bad_lines='warn')
    except pd.errors.ParserError as e:
        print("Error reading CSV:", e)
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subject', methods=['POST'])
def get_subject():
    grade = request.form.get('grade')
    class_number = request.form.get('class_number')
    student_id = request.form.get('student_id')
    test_time_str = request.form.get('test_time')
    test_day_str = request.form.get('test_day')

    print(f"Received: grade={grade}, class_number={class_number}, student_id={student_id}, test_time={test_time_str}, test_day={test_day_str}")

    student_data = get_sheet_data(STUDENT_SHEET_URL)
    timetable_data = get_sheet_data(TIMETABLE_SHEET_URL)

    if not grade or not class_number or not student_id:
        return 'Missing required fields.', 400

    if student_data is None or timetable_data is None:
        return 'Error reading Google Sheets data.'

    test_time = datetime.datetime.strptime(test_time_str, "%H:%M").time() if test_time_str else None
    test_day = int(test_day_str) if test_day_str else None

    current_subject = find_current_subject(grade, class_number, student_id, student_data, timetable_data, test_time, test_day)

    return render_template('subject.html', subject=current_subject)

def find_current_subject(grade, class_number, student_id, student_data, timetable_data, test_time=None, test_day=None):
    now = datetime.datetime.now()
    current_day = test_day if test_day is not None else now.weekday()  # 월요일=0, 일요일=6
    current_time = test_time if test_time else now.time()

    # 요일 맵핑
    days = ['월', '화', '수', '목', '금']

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

    # 쉬는 시간
