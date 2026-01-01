import sys
import io
from django.http import JsonResponse
from django.shortcuts import render
import os

print("=== pycode 위치 ===")
print(os.path.dirname(__file__))

def editor(request):
    return render(request, 'pycode/editor.html')


def run_code(request):
    code = request.POST.get('code', '')

    # print 출력 캡처
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        exec(code, {})
        output = sys.stdout.getvalue()
    except Exception as e:
        output = str(e)

    sys.stdout = old_stdout

    return JsonResponse({'output': output})
