from flask import Flask, render_template, request
import pandas as pd
import datetime

app = Flask(__name__)

# Google Sheets URLs
STUDENT_SHEET_URL = 'https://docs.google.com/spreadsheets/d/11RqrhH7lIUnCmOFM0RPZeqcMHT_OVGiFjMzfByJQCJw/export?format=csv'
TIMETABLE_SHEET_URL = 'https://docs.google.com/spreadsheets/d/1Fydu0QvrnIMI3qAwKYh5vcD42b-slxa2QBnJx-8h9uo/export?format=csv'

# Load data
try:
    student_data = pd.read_csv(STUDENT_SHEET_URL, encoding='utf-8', header=2)
    student_data = student_data[1:]  # 첫 번째 행 제거
    student_data.columns = ['학년', '반', '번호', '교양', 'A', 'B', 'C', 'D', 'E', 'F']
    student_data = student_data.applymap(str)  # 모든 데이터를 문자열로 변환
    timetable_data = pd.read_csv(TIMETABLE_SHEET_URL, encoding='utf-8', header=0)
except Exception as e:
    print("Error loading data:", e)
    student_data = pd.DataFrame()
    timetable_data = pd.DataFrame()

# Display the dataframes to ensure they are loaded correctly
print("Student Data Columns:")
print(student_data.columns)

print("Timetable Data Columns:")
print(timetable_data.columns)

print("Student Data:")
print(student_data.head())

print("Timetable Data:")
print(timetable_data.head())

def find_current_subject(grade, class_number, student_id, student_data, timetable_data, test_time=None, test_day=None):
    now = datetime.datetime.now()
    current_day = test_day if test_day is not None else now.weekday()  # 월요일=0, 일요일=6
    current_time = test_time if test_time else now.time()

    print(f"Current Day: {current_day}, Current Time: {current_time}")  # 디버깅용

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

    print(f"Period Index: {period_index}")  # 디버깅용

    # 쉬는 시간일 경우 다음 교시로 변경
    if period_index == -1:
        for i, (start, end) in enumerate(periods):
            if current_time < start:
                period_index = i
                break

    print(f"Adjusted Period Index: {period_index}")  # 디버깅용

    # 현재 교시가 마지막 교시 이후인 경우
    if period_index == -1 or period_index >= len(periods):
        return "No class at this time"

    # 현재 요일과 교시에 맞는 시간표 정보 가져오기
    try:
        current_code = timetable_data.loc[period_index, days[current_day]]
        print(f"Current code: {current_code}")  # 디버깅용
        # 바로 출력 가능한 과목들
        immediate_subjects = ['확률과 통계', '영어 독해와 작문', '환경', '미술창작', '스포츠', '동아리', '자치']
        if current_code in ['a', 'b', 'c', 'd', 'e', 'f', '교양']:
            # 학생의 선택과목 찾기
            student_row = student_data[(student_data['학년'] == str(grade)) & 
                                       (student_data['반'] == str(class_number)) & 
                                       (student_data['번호'] == str(student_id))]
            print(f"Filtered Student Row: {student_row}")  # 디버깅용
            if student_row.empty:
                print("Student ID not found")
                return "Student ID not found"

            student_subjects = student_row.iloc[0].to_dict()
            print(f"Student subjects: {student_subjects}")  # 디버깅용
            current_subject = student_subjects.get(current_code, "Unknown Subject")
        elif current_code in immediate_subjects:
            current_subject = current_code
        else:
            current_subject = "Unknown Subject"
    except (IndexError, KeyError) as e:
        print(f"Error: {e}")  # 디버깅용
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

    print(f"Received: grade={grade}, class_number={class_number}, student_id={student_id}, test_time={test_time_str}, test_day={test_day_str}")

    if not grade or not class_number or not student_id:
        return 'Missing required fields.', 400

    try:
        test_time = datetime.datetime.strptime(test_time_str, "%H:%M").time() if test_time_str else None
    except ValueError:
        return 'Invalid time format. Please use HH:MM format.', 400

    days_mapping = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4}
    test_day = days_mapping.get(test_day_str) if test_day_str else None

    current_subject = find_current_subject(int(grade), int(class_number), int(student_id), student_data, timetable_data, test_time, test_day)

    return render_template('subject.html', subject=current_subject)

if __name__ == '__main__':
    app.run(debug=True)
