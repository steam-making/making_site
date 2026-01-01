from django.db import models
from django.contrib.auth.models import User
from teachers.models import TeachingInstitution
from django.utils import timezone


class VendorType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Vendor(models.Model):
    name = models.CharField("거래처명", max_length=100)
    vendor_type = models.ForeignKey(VendorType, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="종류")
    contact = models.CharField("연락처", max_length=50, blank=True)
    address = models.CharField("주소", max_length=200, blank=True)

    def __str__(self):
        return self.name


class Material(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="거래처명")
    name = models.CharField(max_length=100, verbose_name="교구재 이름")
    vendor_type = models.ForeignKey(VendorType, on_delete=models.CASCADE, verbose_name="거래처 종류")
    consumer_price = models.PositiveIntegerField(verbose_name="소비자가", default=0)
    school_price = models.PositiveIntegerField(verbose_name="학교납품가", default=0)
    institute_price = models.PositiveIntegerField(verbose_name="기관납품가", default=0)
    supply_price = models.PositiveIntegerField(verbose_name="공급가", default=0)
    stock = models.PositiveIntegerField(verbose_name="재고", default=0)
    
    # 🔽 거래처별 정렬순서
    vendor_order = models.PositiveIntegerField("거래처 내 순서", default=0)
    
    class Meta:
        ordering = ["vendor", "vendor_order", "name"]

    def __str__(self):
        return f'{self.name} ({self.vendor.name})'


class Order(models.Model):
    ORDER_STATUS = [
        ('ordered', '주문완료'),
        ('waiting', '입고대기'),
        ('received', '입고완료'),
    ]

    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="교구재")
    quantity = models.PositiveIntegerField(verbose_name="수량")

    ordered_date = models.DateField("주문일자", default=timezone.now)
    expected_date = models.DateField("예상 입고일", null=True, blank=True)

    status = models.CharField(max_length=10, choices=ORDER_STATUS, default='ordered')

    # ✅ order_year / order_month 필드 삭제 완료

    def __str__(self):
        return f"{self.material.name} 주문 ({self.quantity}개)"


class Receipt(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    received_date = models.DateField(auto_now_add=True)
    received_quantity = models.PositiveIntegerField()

    def save(self, *args, **kwargs):
        self.order.material.stock += self.received_quantity
        self.order.material.save()
        self.order.status = 'received'
        self.order.save()
        super().save(*args, **kwargs)
        
class MaterialOrder(models.Model):
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="강사ID"
    )
    # institution = models.ForeignKey(TeachingInstitution, on_delete=models.CASCADE, verbose_name="출강 장소")

    ordered_date = models.DateField("주문일자", default=timezone.now)  # ✅ 주문일
    expected_date = models.DateField("예상 입고일", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    # ✅ 주문 단위 입고 종류
    RECEIVE_TYPE_CHOICES = [
        ('order', '주문입고'),
        ('return', '반납입고'),
    ]
    receive_type = models.CharField(
        max_length=10,
        choices=RECEIVE_TYPE_CHOICES,
        default='order',
        verbose_name="입고 종류"
    )

    # ✅ 주문 단위 비고
    notes = models.TextField("비고", blank=True, null=True)

    def __str__(self):
        if self.teacher:
            return f"{self.teacher.first_name} - {self.ordered_date} 주문"
        return f"(주문자 없음) - {self.ordered_date} 주문"


class MaterialRelease(models.Model):
    
    title = models.CharField("견적서 제목", max_length=200, blank=True)
    notes = models.TextField("비고", blank=True)
    
    RELEASE_METHOD_CHOICES = [
        ('택배', '택배'),
        ('센터수령', '센터수령'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('unpaid', '미수금'),
        ('partial', '부분수금'),
        ('paid', '수금완료'),
    ]

    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="강사ID")
    institution = models.ForeignKey(TeachingInstitution, on_delete=models.CASCADE, verbose_name="출강 장소")

    # ✅ 출고에는 주문년월 유지해야 함
    order_month = models.CharField(max_length=7, verbose_name="주문 년월", null=True, blank=True, default="2025-08")

    release_date = models.DateField(auto_now_add=True)
    expected_date = models.DateField("출고 예정일", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    release_method = models.CharField(
        "출고방법",
        max_length=20,
        choices=RELEASE_METHOD_CHOICES,
        default='택배'
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        verbose_name='수금 상태'
    )
    
    payment_date = models.DateField(
        "수금일",
        null=True,
        blank=True
    )

    estimate_sent = models.BooleanField(
        default=False,
        verbose_name="견적서 발행 여부"
    )
    
    tax_invoice_sent = models.BooleanField(
        default=False,
        verbose_name="세금계산서 발행 여부"
    )
    
    # 작성자 필드
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_releases",
        verbose_name="작성자"
    )

    def __str__(self):
        return f"{self.teacher.first_name} - {self.release_date} 출고"

class MaterialOrderItem(models.Model):
    STATUS_CHOICES = [
        ('waiting', '입고대기'),
        ('received', '입고완료'),
    ]
    
    RECEIVE_TYPE_CHOICES = [
        ('order', '주문입고'),
        ('return', '반납입고'),
    ]

    order = models.ForeignKey(MaterialOrder, on_delete=models.CASCADE, related_name='items')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, verbose_name="거래처")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="교구재")
    quantity = models.PositiveIntegerField(verbose_name="수량")

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='waiting'
    )
    received_date = models.DateField(null=True, blank=True)
    
    # ✅ 입고 종류 (주문입고 / 반납입고)
    receive_type = models.CharField(
        max_length=10,
        choices=RECEIVE_TYPE_CHOICES,
        default='order',
        verbose_name="입고 종류"
    )
    
    notes = models.TextField(blank=True, null=True, verbose_name="비고")

    # ✅ 입금일자 필드
    paid_date = models.DateField(null=True, blank=True, verbose_name="입금일자")

    def __str__(self):
        return f"{self.material.name} x {self.quantity}"

    @property
    def payment_status(self):
        if self.paid_date:
            return "입금완료"
        return "미입금"


class MaterialReleaseItem(models.Model):
    RELEASE_METHOD_CHOICES = [
        ('택배', '택배'),
        ('센터수령', '센터수령'),
    ]

    release = models.ForeignKey('MaterialRelease', on_delete=models.CASCADE, related_name="items")
    vendor = models.ForeignKey('materials.Vendor', on_delete=models.CASCADE)
    material = models.ForeignKey('materials.Material', on_delete=models.CASCADE)
    unit_price = models.PositiveIntegerField("납품가", default=0)
    quantity = models.PositiveIntegerField()
    status = models.CharField(
        max_length=10,
        choices=[('pending', '출고대기'), ('released', '출고완료')],
        default='pending'
    )
    release_method = models.CharField(
        "출고방법",
        max_length=20,
        choices=RELEASE_METHOD_CHOICES,
        default='택배'
    )
    released_at = models.DateTimeField(null=True, blank=True)
    included = models.BooleanField("견적 포함 여부", default=True)
    group_name = models.CharField("품명(묶음표시)", max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.material.name} x {self.quantity} ({self.release_method})"


class ReleasePaymentStatus(models.Model):
    STATUS_CHOICES = (
        ('unpaid', '미수금'),
        ('paid', '수금완료'),
    )
    institution = models.ForeignKey(
        TeachingInstitution, on_delete=models.CASCADE, related_name='release_payments'
    )
    order_month = models.CharField(max_length=7)  # 'YYYY-MM'

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')

    class Meta:
        unique_together = ('institution', 'order_month')

    def __str__(self):
        return f'{self.institution.name} - {self.order_month} - {self.get_status_display()}'

from django.db import models
from django.conf import settings

class MaterialHistory(models.Model):
    material = models.ForeignKey("Material", on_delete=models.CASCADE, related_name="histories")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    change_type = models.CharField(max_length=50, choices=[
        ("create", "등록"),
        ("update", "수정"),
        ("delete", "삭제"),
        ("stock_increase", "수량 증가"),
        ("stock_decrease", "수량 감소"),
    ])
    old_value = models.IntegerField(null=True, blank=True)
    new_value = models.IntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)  # 변경 사유
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.change_type}] {self.material.name} {self.old_value} → {self.new_value}"
