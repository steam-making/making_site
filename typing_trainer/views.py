import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from .models import TypingStage, TypingResult


@login_required
def home(request):
    stages = TypingStage.objects.order_by("order", "stage_type", "language")
    return render(request, "typing_trainer/home.html", {"stages": stages})


@login_required
def practice(request, stage_id):
    stage = get_object_or_404(TypingStage, pk=stage_id)

    # 자리연습(1번) 화면만 우선 구현
    if stage.stage_type != "POSITION":
        # 추후 낱말/단문/장문은 여기서 분기
        return render(
            request,
            "typing_trainer/not_ready.html",
            {"stage": stage},
        )

    chars = [c.strip() for c in (stage.practice_chars or "").split(",") if c.strip()]
    if not chars:
        chars = ["ㅁ", "ㄴ", "ㅇ", "ㄹ"] if stage.language == "KO" else ["a", "s", "d", "f"]

    print("🔥 FINAL chars =", chars)

    context = {
        "stage": stage,
        "chars_json": json.dumps(chars, ensure_ascii=False),
    }
    return render(request, "typing_trainer/position_practice.html", context)


def _calc_pass(stage: TypingStage, speed: int, accuracy: float, typo_count: int) -> bool:
    return (
        speed >= stage.min_speed
        and accuracy >= stage.min_accuracy
        and typo_count <= stage.max_typo
    )


@login_required
def save_result(request, stage_id):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    stage = get_object_or_404(TypingStage, pk=stage_id)

    try:
        payload = json.loads(request.body.decode("utf-8"))
        speed = int(payload.get("speed", 0))
        accuracy = float(payload.get("accuracy", 0))
        typo_count = int(payload.get("typo_count", 0))
        duration = int(payload.get("duration", stage.duration_seconds))
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    passed = _calc_pass(stage, speed, accuracy, typo_count)

    TypingResult.objects.create(
        user=request.user,
        stage=stage,
        speed=speed,
        accuracy=accuracy,
        typo_count=typo_count,
        duration=duration,
        passed=passed,
    )

    return JsonResponse({"ok": True, "passed": passed})
