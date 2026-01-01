from django.contrib import admin
from .models import LottoResult

@admin.register(LottoResult)
class LottoResultAdmin(admin.ModelAdmin):
    list_display = ("draw_no", "numbers", "bonus")
    ordering = ("-draw_no",)
    search_fields = ("draw_no", "numbers")
