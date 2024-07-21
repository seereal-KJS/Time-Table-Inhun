from flask import Flask, render_template, request
import pandas as pd
import datetime

app = Flask(__name__)

# Google Sheets 설정
STUDENT_SHEET_URL = 'https://docs.google.com/spreadsheets/d/11RqrhH7lIUnCmOFM0RPZeqcMHT_OVGiFjMzfByJQCJw/edit?usp=sharing'
TIMETABLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fydu0QvrnIMI3qAwKYh5vcD42b-slxa2QBnJx-8h9uo/edit?usp=sharing'

def get_sheet_data(url):
    return pd.read_csv(url)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subject', methods=['POST'])
def get_subject():
    student_id = request.form['student_id']
    student_data = get_sheet_data(STUDENT_SHEET_URL)
    timetable_data = get_sheet_data(TIMETABLE_SHEET_URL)

    selected_subjects = find_selected_subjects(student_id, student_data)
    if selected_subjects is None:
        return 'Student ID not found.'

    current_subject = find_current_subject(selected_subjects, timetable_data)

    return render_template('subject.html', subject=current_subject)

def find_selected_subjects(student_id, student_data):
    student_row = student_data[student_data['Student ID'] == student_id]
    if not student_row.empty:
        return student_row.iloc[0].to_dict()
    return None

def find_current_subject(selected_subjects, timetable_data):
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

    if period_index == -1:
        return "No class at this time"

    # 현재 요일의 시간표 정보 가져오기
    if current_day < len(timetable_data) and period_index + 1 < len(timetable_data):
        return timetable_data.iloc[period_index + 1, current_day + 1]
    else:
        return "No class at this time"

if __name__ == '__main__':
    app.run(debug=True)

