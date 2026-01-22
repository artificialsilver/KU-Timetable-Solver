from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# 데이터 로드
with open('parsed_subjects.json', 'r', encoding='utf-8') as f:
    all_data = json.load(f)

def is_conflict(current_schedule, next_subject):
    for subject in current_schedule:
        for t1 in subject['parsed_times']:
            for t2 in next_subject['parsed_times']:
                if t1['day'] == t2['day'] and (set(t1['periods']) & set(t2['periods'])):
                    return True
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve_api():
    data = request.json
    raw_inputs = [i.strip().upper() for i in data.get('subjects', '').split(",") if i.strip()]
    min_courses = int(data.get('min_courses', 1))
    required_codes = [i.strip().upper() for i in data.get('required', '').split(",") if i.strip()]

    # 과목 그룹화 로직 (기존 코드 활용)
    course_groups = {}
    for item in raw_inputs:
        # ... (기존 solve()의 그룹화 로직 동일하게 적용) ...
        if "-" in item:
            if item in all_data:
                code = all_data[item]["code"]
                if code not in course_groups: course_groups[code] = set()
                course_groups[code].add(item)
        else:
            for fid, info in all_data.items():
                if info["code"] == item:
                    if item not in course_groups: course_groups[item] = set()
                    course_groups[item].add(fid)

    group_keys = list(course_groups.keys())
    for key in group_keys: course_groups[key] = list(course_groups[key])

    all_results = []
    required_found_in_keys = [k for k in required_codes if k in group_keys]

    def backtrack(idx, current_schedule):
        if idx == len(group_keys):
            current_codes = [s['code'] for s in current_schedule]
            if len(current_schedule) >= min_courses and all(rc in current_codes for rc in required_found_in_keys):
                all_results.append(list(current_schedule))
            return
        
        # 선택 1: 추가
        current_course_code = group_keys[idx]
        for fid in course_groups[current_course_code]:
            if not is_conflict(current_schedule, all_data[fid]):
                current_schedule.append(all_data[fid])
                backtrack(idx + 1, current_schedule)
                current_schedule.pop()
        
        # 선택 2: 건너뛰기
        backtrack(idx + 1, current_schedule)

    backtrack(0, [])
    all_results.sort(key=len, reverse=True)
    
    return jsonify(all_results[:30]) # 상위 30개만 반환

if __name__ == '__main__':
    # 0.0.0.0으로 설정해야 외부 접속이 가능합니다.
    app.run(host='0.0.0.0', port=5000)