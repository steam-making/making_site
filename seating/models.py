from django.db import models
from teachers.models import TeachingInstitution
from students.models import ProgramDivision


class SeatLayout(models.Model):
    """학교(출강장소) 1곳당 1개의 자리배치. 1부/2부/3부가 같은 교실을 쓰므로 부서 공통으로 관리한다.
    행마다 조 개수(열 수)가 다를 수 있어 콤마로 구분된 문자열로 저장한다. (예: "4,3,5" = 1행 4조, 2행 3조, 3행 5조)"""
    institution = models.OneToOneField(
        TeachingInstitution, on_delete=models.CASCADE, related_name='seat_layout'
    )
    row_col_counts = models.CharField("행별 조 열 수", max_length=200, default="2,2")
    updated_at = models.DateTimeField(auto_now=True)

    def get_row_col_counts(self):
        result = []
        for token in self.row_col_counts.split(','):
            token = token.strip()
            if token.isdigit() and int(token) > 0:
                result.append(int(token))
        return result or [2]

    @property
    def group_rows(self):
        return len(self.get_row_col_counts())

    def __str__(self):
        return f"{self.institution.name} 자리배치"


class SeatGroup(models.Model):
    """레이아웃 안의 조(책상 그룹) 1개. 조마다 좌석 행/열을 다르게 설정할 수 있다."""
    layout = models.ForeignKey(SeatLayout, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField("조 이름", max_length=50)
    position_row = models.PositiveIntegerField("배치 행")
    position_col = models.PositiveIntegerField("배치 열")
    seat_rows = models.PositiveIntegerField("조 내 좌석 행 수", default=2)
    seat_cols = models.PositiveIntegerField("조 내 좌석 열 수", default=2)

    class Meta:
        ordering = ['position_row', 'position_col']
        unique_together = ('layout', 'position_row', 'position_col')

    def __str__(self):
        return f"{self.layout.institution.name} - {self.name}"


class Seat(models.Model):
    """조 안의 물리적인 좌석 1자리. 1부/2부/3부가 같은 좌석을 공유하고,
    실제로 누가 앉는지는 SeatAssignment(부서별 배정)로 따로 관리한다."""
    group = models.ForeignKey(SeatGroup, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.PositiveIntegerField("조 내 좌석 번호")

    class Meta:
        ordering = ['seat_number']

    def __str__(self):
        return f"{self.group.name} - 좌석 {self.seat_number}"


class SeatAssignment(models.Model):
    """부서(1부/2부/3부)별 좌석-학생 배정"""
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='assignments')
    division = models.ForeignKey(ProgramDivision, on_delete=models.CASCADE, related_name='seat_assignments')
    student = models.OneToOneField(
        'students.Student', on_delete=models.CASCADE, related_name='seat_assignment'
    )

    class Meta:
        unique_together = ('seat', 'division')

    def __str__(self):
        return f"{self.division} - {self.seat} - {self.student.name}"
