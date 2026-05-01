import os
import django

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'making_site.settings')
django.setup()

from main.models import MenuItem
from django.contrib.sites.models import Site

def populate_menus():
    # --- [도메인 설정] 사이트맵 주소용 ---
    site = Site.objects.get_current()
    if site.domain != "steam-making.com":
        site.domain = "steam-making.com"
        site.name = "메듀사(MeduTeacher)"
        site.save()
        print(f"사이트 도메인이 {site.domain}으로 설정되었습니다.")

    # 전체 삭제 후 재생성 (그룹화 버전)
    MenuItem.objects.all().delete()

    print("메뉴 그룹화 및 최적화를 시작합니다...")

    # --- [정보/소개] 그룹 (하나로 묶음) ---
    m_info = MenuItem.objects.get_or_create(title="정보", url="#", icon_class="bi-info-circle-fill", order=1, access_level="all")[0]
    MenuItem.objects.get_or_create(title="소개", url="/#about", order=1, parent=m_info, access_level="all")
    MenuItem.objects.get_or_create(title="출강안내", url="/#field", order=2, parent=m_info, access_level="all")
    MenuItem.objects.get_or_create(title="자격안내", url="/#certification", order=3, parent=m_info, access_level="all")
    MenuItem.objects.get_or_create(title="공지사항", url="/notices/", order=4, parent=m_info, access_level="all")

    # --- [관리자 전용] 관리 ---
    m_admin = MenuItem.objects.get_or_create(title="관리", url="#", icon_class="bi-gear-fill", order=100, access_level="staff")[0]
    MenuItem.objects.get_or_create(title="공지사항 관리", url="/notices/", order=1, parent=m_admin, access_level="staff")
    MenuItem.objects.get_or_create(title="회원승인", url="/accounts/approve_users/", order=2, parent=m_admin, access_level="staff")
    MenuItem.objects.get_or_create(title="회원목록", url="/accounts/members/", order=3, parent=m_admin, access_level="staff")
    MenuItem.objects.get_or_create(title="미디어관리", url="/admin/filebrowser/browse/", order=4, parent=m_admin, access_level="staff")
    MenuItem.objects.get_or_create(title="메뉴관리", url="/menu-management/", order=99, parent=m_admin, access_level="staff")

    # --- [교구재] (관리자+강사 공용) ---
    m_mat = MenuItem.objects.get_or_create(title="교구재", url="#", icon_class="bi-box-seam", order=105, access_level="teacher")[0]
    MenuItem.objects.get_or_create(title="교구목록", url="/materials/", order=1, parent=m_mat, access_level="staff")
    MenuItem.objects.get_or_create(title="교구입고", url="/materials/orders/", order=2, parent=m_mat, access_level="staff")
    MenuItem.objects.get_or_create(title="교구출고", url="/materials/releases/", order=3, parent=m_mat, access_level="teacher")
    MenuItem.objects.get_or_create(title="교구반납", url="/materials/returns/", order=4, parent=m_mat, access_level="teacher")

    # --- [강사용] ---
    m_recruit = MenuItem.objects.get_or_create(title="모집", url="#", icon_class="bi-megaphone-fill", order=110, access_level="teacher")[0]
    MenuItem.objects.get_or_create(title="모집공고(광주)", url="/linkhub/?area=gwangju", order=1, parent=m_recruit, access_level="teacher")
    MenuItem.objects.get_or_create(title="모집공고(전남)", url="/linkhub/?area=jeonnam", order=2, parent=m_recruit, access_level="teacher")
    
    m_student = MenuItem.objects.get_or_create(title="학생", url="#", icon_class="bi-people-fill", order=120, access_level="teacher")[0]
    MenuItem.objects.get_or_create(title="학생관리", url="/students/list/", order=1, parent=m_student, access_level="teacher")
    MenuItem.objects.get_or_create(title="단계업관리", url="/robot_LvUP/", order=2, parent=m_student, access_level="teacher")

    m_history = MenuItem.objects.get_or_create(title="이력", url="#", icon_class="bi-journal-bookmark", order=130, access_level="teacher")[0]
    MenuItem.objects.get_or_create(title="출강장소", url="/teachers/institutions/", order=1, parent=m_history, access_level="teacher")
    MenuItem.objects.get_or_create(title="경력관리", url="/teachers/careers/", order=2, parent=m_history, access_level="teacher")
    MenuItem.objects.get_or_create(title="자격증관리", url="/teachers/certificates/", order=3, parent=m_history, access_level="teacher")

    # --- [기관용] ---
    m_inst = MenuItem.objects.get_or_create(title="기관", url="#", icon_class="bi-building", order=140, access_level="institution")[0]
    MenuItem.objects.get_or_create(title="프로그램목록", url="/products/", order=1, parent=m_inst, access_level="institution")
    MenuItem.objects.get_or_create(title="예약리스트", url="/reservations/", order=2, parent=m_inst, access_level="institution")
    MenuItem.objects.get_or_create(title="예약캘린더", url="/reservations/calendar/", order=3, parent=m_inst, access_level="institution")

    # --- [관리자용 유틸] ---
    m_util = MenuItem.objects.get_or_create(title="유틸", url="#", icon_class="bi-tools", order=160, access_level="staff")[0]
    MenuItem.objects.get_or_create(title="로또추천", url="/lotto/", order=1, parent=m_util, access_level="staff")
    MenuItem.objects.get_or_create(title="QR링크", url="/q/", order=2, parent=m_util, access_level="staff")

    print("그룹화 완료. 상단 바가 훨씬 깔끔해졌습니다.")

if __name__ == "__main__":
    populate_menus()
