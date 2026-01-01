from django import forms
from .models import Task, WorkType

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'work_type', 'due_date', 'repeat']  # ✅ repeat 추가
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'repeat': forms.Select(attrs={'class': 'form-select'}),  # ✅ Bootstrap5 스타일 적용
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ 업무종류가 비어 있을 때 기본으로 첫 번째 WorkType 선택
        if not self.instance.pk:  # 새로 추가하는 경우만
            first_type = WorkType.objects.order_by('order').first()
            if first_type:
                self.fields['work_type'].initial = first_type

        # ✅ 필드 라벨 및 도움말 커스터마이징
        self.fields['repeat'].label = "반복 주기"
        self.fields['repeat'].help_text = "반복 설정 시 완료 시 다음 주기 할 일이 자동 생성됩니다."
