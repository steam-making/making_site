import ast
from django.http import JsonResponse


###########################################################
# 🔧 안전한 AST child 순회 (문자열/숫자 방지)
###########################################################
def safe_iter_child_nodes(node):
    """node 가 AST일 때만 iterate"""
    if isinstance(node, ast.AST):
        return ast.iter_child_nodes(node)
    return []


###########################################################
# 🔍 1) input() 개수 계산 (중첩 for 지원)
###########################################################
def count_inputs(node):
    """
    AST 내부의 input() 호출 횟수를 정확히 계산.
    - for range(N) → input 횟수 × N
    - 중첩 for/while 지원
    - 문자열 literal 있는 node 안전 처리
    """

    # 문자열, 숫자 등 literal은 처리 제외
    if not isinstance(node, ast.AST):
        return 0

    total = 0

    # input() 직접 호출
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "input":
        return 1

    # for range(N) 반복문 처리
    if isinstance(node, ast.For):
        repeat = 1

        # range(N) 인지 확인
        if isinstance(node.iter, ast.Call):
            func = node.iter.func
            args = node.iter.args

            if isinstance(func, ast.Name) and func.id == "range":
                # range(N)
                if (
                    len(args) == 1 and 
                    isinstance(args[0], ast.Constant) and 
                    isinstance(args[0].value, int)
                ):
                    repeat = args[0].value

                # range(a, b)
                elif (
                    len(args) == 2 and
                    isinstance(args[0], ast.Constant) and isinstance(args[1], ast.Constant)
                ):
                    start = args[0].value
                    end = args[1].value
                    if isinstance(start, int) and isinstance(end, int):
                        repeat = max(0, end - start)

        # 반복문 내부 input 계산
        body_inputs = sum(
            count_inputs(child) 
            for child in node.body 
            if isinstance(child, ast.AST)
        )

        return repeat * body_inputs

    # 기타 노드: 모든 하위 노드 체크
    for child in safe_iter_child_nodes(node):
        total += count_inputs(child)

    return total


###########################################################
# 🔍 2) API: input 개수 반환
###########################################################
def api_count_input(request):
    code = request.POST.get("code", "")

    try:
        tree = ast.parse(code)
    except Exception:
        return JsonResponse({"count": 0})

    count = count_inputs(tree)
    return JsonResponse({"count": count})


###########################################################
# 🔥 3) 무한 루프 감지 (while True / while 1)
###########################################################
def detect_infinite_loop(code):
    """
    무한 루프 가능성 감지:
    - while True
    - while 1
    - while 변수 기반 (True로만 설정된 경우)
    """

    try:
        tree = ast.parse(code)
    except:
        return False

    infinite = False

    class LoopChecker(ast.NodeVisitor):
        def visit_While(self, node):
            nonlocal infinite

            # while True:
            if isinstance(node.test, ast.Constant) and node.test.value == True:
                infinite = True
            
            # while 1:
            if isinstance(node.test, ast.Constant) and node.test.value == 1:
                infinite = True

            # while x: (x가 True literal일 경우)
            if isinstance(node.test, ast.Name):
                if node.test.id in ["True", "true"]:
                    infinite = True

            self.generic_visit(node)

    LoopChecker().visit(tree)
    return infinite
