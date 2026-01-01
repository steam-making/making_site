# pycourse/api/precheck.py
import ast
import builtins
import re
import sys
import io

from django.http import JsonResponse


###########################################################
# 🔍 1) input() 개수 정확히 계산
###########################################################
def count_inputs(node):
    """
    AST 내부의 input() 호출 횟수를 계산.
    for range(N) → N배 분석
    중첩 for도 자동 계산
    """

    total = 0

    # input() 함수 직접 호출
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
        return 1

    # for 반복문 처리
    if isinstance(node, ast.For):
        repeat = 1

        # range(N) 반복 횟수 탐지
        if (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
        ):
            args = node.iter.args
            if len(args) == 1 and isinstance(args[0], ast.Constant):
                repeat = args[0].value

        # 내부 input 계산
        inside = sum(count_inputs(child) for child in node.body)

        return repeat * inside

    # 기본: 모든 자식 노드 탐색
    for child in ast.iter_child_nodes(node):
        total += count_inputs(child)

    return total


###########################################################
# 🔍 2) 무한 루프 가능성 탐지 (기본)
###########################################################
def detect_infinite_loop(code):
    # while True:  / while(True): / while  (  True   ):
    pattern = r"while\s*\(?\s*True\s*\)?:"
    if re.search(pattern, code):
        return True
    return False


###########################################################
# 🔍 3) 사전 검사 API
###########################################################
def api_precheck(request):
    code = request.POST.get("code", "")

    try:
        tree = ast.parse(code)
    except Exception:
        return JsonResponse({"possible_infinite": False, "input_count": 0})

    infinite = detect_infinite_loop(code)
    input_count = count_inputs(tree)

    return JsonResponse({
        "possible_infinite": infinite,
        "input_count": input_count,
    })


###########################################################
# 🔥 4) 실행 API (input 지원 + 반복 제한)
###########################################################
def api_run(request):
    code = request.POST.get("code", "")

    # ⭐ input_value 받기
    input_raw = request.POST.get("input_value", "")
    user_inputs = input_raw.split("\n") if input_raw else []

    # ⭐ JS에서 보낸 전체 input 개수 받기
    required_inputs = request.POST.get("required_inputs")
    if required_inputs:
        required_inputs = int(required_inputs)
    else:
        required_inputs = None

    # 반복 제한
    loop_limit = request.POST.get("loop_limit")
    if loop_limit:
        loop_limit = int(loop_limit)
    else:
        loop_limit = 999999

    # ⭐ required_inputs 전달
    output = execute_python_with_limit(
        code,
        loop_limit,
        user_inputs,
        required_inputs
    )

    return JsonResponse({"output": output})




###########################################################
# 🧠 5) 파이썬 실행 엔진 (AST 기반 제한 + input 지원)
###########################################################
def execute_python_with_limit(code, limit, user_inputs, required_inputs):
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    input_index = {"i": 0}
    loop_counter = {"count": 0}

    def safe_input(prompt=""):
        required_count = input_index["i"] + 1
        provided_count = len(user_inputs)

        # ⭐ 전체 필요 input 기준으로 부족 계산
        if required_inputs and provided_count < required_inputs:
            missing = required_inputs - provided_count
            raise Exception(
                f"입력 값이 부족합니다.\n"
                f"필요한 전체 입력 개수: {required_inputs}개\n"
                f"제공한 입력 개수: {provided_count}개\n"
                f"→ 부족한 입력: {missing}개"
            )

        # 실행 중 호출 횟수 기준 부족 계산
        if required_count > provided_count:
            missing = required_count - provided_count
            raise Exception(
                f"입력 값이 부족합니다.\n"
                f"input()은 현재 {required_count}번째 호출 중입니다.\n"
                f"제공된 입력: {provided_count}개\n"
                f"→ 부족한 입력: {missing}개"
            )

        val = user_inputs[input_index["i"]]
        input_index["i"] += 1
        print(val)
        return val


    ###########################################################
    # ✏️ AST 기반 반복문 감시 (제한 초과 시 Exception)
    ###########################################################
    class LoopLimiter(ast.NodeTransformer):
        def visit_While(self, node):
            node = self.generic_visit(node)

            # print 실행 → 그 다음에 반복 횟수 검사
            check = ast.parse(
                "loop_counter['count'] += 1\n"
                "if loop_counter['count'] >= LIMIT:\n"
                "    raise Exception('반복 제한 초과')"
            ).body

            node.body = node.body + check
            return node

        def visit_For(self, node):
            node = self.generic_visit(node)

            check = ast.parse(
                "loop_counter['count'] += 1\n"
                "if loop_counter['count'] >= LIMIT:\n"
                "    raise Exception('반복 제한 초과')"
            ).body

            node.body = node.body + check
            return node

    ###########################################################
    # ✏️ AST 변환 + 안전 실행
    ###########################################################
    try:
        tree = ast.parse(code)
        tree = LoopLimiter().visit(tree)
        ast.fix_missing_locations(tree)

        safe_globals = {
            "LIMIT": limit,
            "loop_counter": loop_counter,
            "input": safe_input,
            "__builtins__": {
                name: getattr(builtins, name)
                for name in dir(builtins)
            }
        }

        exec(compile(tree, filename="<ast>", mode="exec"), safe_globals, {})

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output

    except Exception as e:
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        return output + f"\n{str(e)}"
