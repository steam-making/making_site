from datetime import date
import io
import sys

def is_child_in_target(child, program):
    """자녀가 프로그램 대상 범위에 속하는지 확인"""
    if not child.birth_date:
        return False

    # 오늘 기준 나이 계산
    today = date.today()
    age = today.year - child.birth_date.year - (
        (today.month, today.day) < (child.birth_date.month, child.birth_date.day)
    )
    print(age,program.target_start.age,program.target_end.age)
    # 프로그램이 참조하는 대상(Target)에 age 값이 있을 경우 비교
    if program.target_start and program.target_start.age and age < program.target_start.age:
        return False
    if program.target_end and program.target_end.age and age > program.target_end.age:
        return False

    return True

def safe_exec(code):
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()

    try:
        exec(code, {"__builtins__": { "print": print, "range": range }})
        output = captured.getvalue()
    except Exception as e:
        output = str(e)

    sys.stdout = old_stdout
    return output