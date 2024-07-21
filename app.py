from flask import Flask, render_template, request
import pandas as pd
import datetime

app = Flask(__name__)

# 공개된 Google 스프레드시트 URL
STUDENT_SHEET_URL = 'https://docs.google.com/spreadsheets/d/11RqrhH7lIUnCmOFM0RPZeqcMHT_OVGiFjMzfByJQCJw/export?format=csv'
TIMETABLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fydu0QvrnIMI3qAwKYh5vcD42b-slxa2QBnJx-8h9uo/export?format=csv'

# 스프레드시트 데이터 로드
student_data = pd.read_csv(STUDENT_SHEET_URL)
timetable_data = pd.read_csv(TIMETABLE_SHEET_URL)

def find_current_subject(grade, class_number, student_id, student_data, timetable_data, test_time=None, test_day=None):
    now = datetime.datetime.now()
    current_day = test_day if test_day is not None else now.weekday()  # 월요일=0, 일요일=6
    current_time = test_time if test_time else now.time()

    days = ['월', '화', '수', '목', '금']

    periods = [
        (datetime.time(8, 30), datetime.time(9, 20)),
        (datetime.time(9, 30), datetime.time(10, 20)),
        (datetime.time(10, 30), datetime.time(11, 20)),
        (datetime.time(11, 30), datetime.time(12, 20)),
        (datetime.time(13, 20), datetime.time(14, 10)),
        (datetime.time(14, 20), datetime.time(15, 10)),
        (datetime.time(15, 20), datetime.time(16, 10)),
    ]

    period_index = -1
    for i, (start, end) in enumerate(periods):
        if start <= current_time <= end:
            period_index = i
            break

    if period_index == -1:
        for i, (start, end) in enumerate(periods):
            if current_time < start:
                period_index = i
                break

    if period_index == -1 or period_index >= len(periods):
        return "No class at this time"

    try:
        current_code = timetable_data.loc[period_index, days[current_day]]
        immediate_subjects = ['확률과 통계', '영어 독해와 작문', '환경', '미술창작', '스포츠', '동아리', '자치']
        if current_code in ['A', 'B', 'C', 'D', 'E', 'F', '교양']:
            student_row = student_data[(student_data['학년'].astype(str) == grade) & 
                                       (student_data['반'].astype(str) == class_number) & 
                                       (student_data['번호'].astype(str) == student_id)]
            if student_row.empty:
                return "Student ID not found"
            student_subjects = student_row.iloc[0].to_dict()
            current_subject = student_subjects.get(current_code, "Unknown Subject")
        elif current_code in immediate_subjects:
            current_subject = current_code
        else:
            current_subject = "Unknown Subject"
    except (IndexError, KeyError) as e:
        return "No class at this time"

    return current_subject

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

    if not grade or not class_number or not student_id:
        return 'Missing required fields.', 400

    try:
        test_time = datetime.datetime.strptime(test_time_str, "%H:%M").time() if test_time_str else None
    except ValueError:
        return 'Invalid time format. Please use HH:MM format.', 400

    days_mapping = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4}
    test_day = days_mapping.get(test_day_str) if test_day_str else None

    current_subject = find_current_subject(str(grade), str(class_number), str(student_id), student_data, timetable_data, test_time, test_day)

    return render_template('subject.html', subject=current_subject)

if __name__ == '__main__':
    app.run(debug=True)
