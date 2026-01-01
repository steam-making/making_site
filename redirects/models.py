from django.db import models

class DynamicLink(models.Model):
    key = models.CharField(max_length=50, unique=True)   # recruit, summer 등
    url = models.URLField()                              # 실제 최종 연결 URL
    title = models.CharField(max_length=200, blank=True) # 관리용 제목 (선택)
    is_active = models.BooleanField(default=True)        # 비활성 시 리디렉션 중단
    click_count = models.PositiveIntegerField(default=0) # 클릭 횟수
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or f"{self.key} → {self.url}"
