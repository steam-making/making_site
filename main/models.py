from django.db import models

class MenuItem(models.Model):
    ACCESS_LEVELS = (
        ('all', '누구나'),
        ('teacher', '강사용'),
        ('institution', '기관용'),
        ('staff', '관리자용'),
    )

    title = models.CharField("메뉴 제목", max_length=100)
    url = models.CharField("이동 URL/뷰이름", max_length=255, blank=True, default="#")
    icon_class = models.CharField("아이콘 클래스", max_length=100, blank=True, help_text="예: bi-gear, bi-people")
    order = models.PositiveIntegerField("출력 순서", default=0)
    is_active = models.BooleanField("활성화 상태", default=True)
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='sub_menus',
        verbose_name="상위 메뉴"
    )
    
    access_level = models.CharField(
        "접근 권한", 
        max_length=20, 
        choices=ACCESS_LEVELS, 
        default='staff'
    )

    class Meta:
        verbose_name = "메뉴 항목"
        verbose_name_plural = "메뉴 항목들"
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} ({self.get_access_level_display()})"
