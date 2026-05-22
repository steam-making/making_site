from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class OpenBankingToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="openbanking_token")
    user_seq_no = models.CharField("오픈뱅킹 사용자일련번호", max_length=50, blank=True)
    access_token = models.TextField("액세스 토큰")
    refresh_token = models.TextField("리프레시 토큰", blank=True)
    expires_at = models.DateTimeField("만료일시")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} 토큰"

    class Meta:
        verbose_name = "오픈뱅킹 토큰"
        verbose_name_plural = "오픈뱅킹 토큰"


class RegisteredAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="registered_accounts")
    fintech_use_num = models.CharField("핀테크이용번호", max_length=100, unique=True)
    bank_code = models.CharField("은행코드", max_length=10)
    bank_name = models.CharField("은행명", max_length=50)
    account_num_masked = models.CharField("마스킹 계좌번호", max_length=50)
    account_holder = models.CharField("예금주", max_length=50, blank=True)
    is_active = models.BooleanField("사용중", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} {self.account_num_masked}"

    class Meta:
        verbose_name = "등록 계좌"
        verbose_name_plural = "등록 계좌"


class BankTransaction(models.Model):
    account = models.ForeignKey(RegisteredAccount, on_delete=models.CASCADE, related_name="transactions")
    tran_date = models.DateField("거래일")
    tran_time = models.CharField("거래시각", max_length=6)
    tran_type = models.CharField("거래구분", max_length=10)  # D=입금, W=출금
    tran_amt = models.BigIntegerField("거래금액")
    balance_amt = models.BigIntegerField("잔액", default=0)
    print_content = models.CharField("거래내용(통장표시)", max_length=200, blank=True)
    branch_name = models.CharField("점명", max_length=100, blank=True)
    tran_unique_no = models.CharField("거래고유번호", max_length=100, unique=True)
    matched_release = models.ForeignKey(
        "materials.MaterialRelease",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="bank_transactions",
        verbose_name="매칭된 출고",
    )
    is_auto_matched = models.BooleanField("자동매칭", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tran_date} {self.print_content} {self.tran_amt:,}원"

    class Meta:
        verbose_name = "은행 거래내역"
        verbose_name_plural = "은행 거래내역"
        ordering = ["-tran_date", "-tran_time"]
