from django.urls import path
from . import views
from .api.parse_input import api_count_input
from .api.precheck import api_precheck, api_run

urlpatterns = [
    path("recruit/", views.program_list, name="program_list"),           # 모집 목록
    path("programs/always/", views.program_list_always, name="program_list_always"),
    path("programs/event/", views.program_list_event, name="program_list_event"),
    path("programs/short/", views.program_list_short, name="program_list_short"),

    path("recruit/<int:pk>/", views.program_detail, name="program_detail"),  # 상세보기
    path("recruit/<int:pk>/apply/", views.program_apply, name="program_apply"),  # 수강신청
    path("programs/new/", views.program_create, name="program_create"),  # 프로그램 등록
    path('<int:pk>/edit/', views.program_edit, name='program_edit'),  # ✅ 수정
    path('<int:pk>/delete/', views.program_delete, name='program_delete'),# ✅ 삭제
    
    path("program/<int:pk>/applications/manage/", views.approve_applications, name="approve_applications"),#신청자 관리 요청
    
    # 목록/상세
    path("products/", views.product_list, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    
    # CRUD
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_update, name="product_update"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    
    # 예약/달력(기존)
    path("reservations/new/", views.reservation_create, name="reservation_create"),
    path("reservations/", views.reservation_list, name="reservation_list"),
    path("reservations/calendar/", views.reservation_calendar, name="reservation_calendar"),
    path("reservations/events/", views.reservation_events, name="reservation_events"),
    path("reservations/<int:pk>/confirm/", views.reservation_confirm, name="reservation_confirm"),
    path("reservations/<int:pk>/cancel/", views.reservation_cancel, name="reservation_cancel"),
    path("reservations/<int:pk>/edit/", views.reservation_edit, name="reservation_edit"),
    
    # ✅ 카테고리 관리용 URL
    path("categories/", views.category_list, name="category_list"),
    path("categories/create/", views.category_create, name="category_create"),
    path("categories/<int:pk>/update/", views.category_update, name="category_update"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    
    path("programs/<int:pk>/clone/", views.program_clone, name="program_clone"),
    
    
    path("targets/", views.target_list, name="target_list"),
    path("targets/create/", views.target_create, name="target_create"),
    path("targets/<int:pk>/update/", views.target_update, name="target_update"),
    path("targets/<int:pk>/delete/", views.target_delete, name="target_delete"),
    path("api/products/<int:pk>/", views.product_detail_api, name="product_detail_api"),
    
    path("my-courses/", views.student_course_list, name="student_course_list"),
    path("my-courses/apply/<str:code>/", views.student_course_apply, name="student_course_apply"),

    # 학생용
    path("student/courses/", views.student_course_list, name="student_course_list"),
    path("student/courses/apply/<int:program_id>/", views.student_course_apply, name="student_course_apply"),

    # 📌 학습 프로그램 목록/CRUD
    path("learning/", views.learning_program_list, name="learning_program_list"),
    path("learning/create/", views.learning_program_create, name="learning_program_create"),
    path("learning/<int:pk>/edit/", views.learning_program_edit, name="learning_program_edit"),
    path("learning/<int:pk>/delete/", views.learning_program_delete, name="learning_program_delete"),

    # 📌 차시(Chapter) 관리
    path("program/<int:pk>/chapters/", views.chapter_manage, name="chapter_manage"),

    # 📌 학생용 코스 보기
    path("<int:program_id>/", views.course_home, name="course_home"),

    # 📌 챕터 상세
    path("chapter/<int:chapter_id>/", views.chapter_detail, name="chapter_detail"),

    # 📌 아이템 상세 페이지
    path("item/<int:item_id>/", views.item_page, name="item_page"),

    # 📌 채점 실행 API
    path("api/precheck/", api_precheck, name="api_precheck"),
    path("api/run/", api_run, name="api_run"),
    path("api/grade/", views.grade_code, name="grade_code"),
    path("api/hint/<int:item_id>/", views.get_hint, name="get_hint"),
    path("api/answer/<int:item_id>/", views.get_answer, name="get_answer"),
    path("api/input-count/", api_count_input, name="api_input_count"),

    path("item/update/<int:item_id>/", views.update_progress, name="update_progress"),


    # 커리큘럼 프로그램 목록
    path(
        "curriculum/",
        views.curriculum_program_list,
        name="curriculum_program_list"
    ),

    # 커리큘럼 프로그램 생성
    path(
        "curriculum/create/",
        views.curriculum_program_create,
        name="curriculum_program_create"
    ),

    # 커리큘럼 프로그램 수정
    path(
        "curriculum/<int:program_id>/edit/",
        views.curriculum_program_update,
        name="curriculum_program_update"
    ),

    # 특정 커리큘럼 프로그램의 차시 목록
    path(
        "curriculum/<int:program_id>/syllabus/",
        views.curriculum_syllabus_list,
        name="curriculum_syllabus_list"
    ),

    # 차시 추가
    path(
        "curriculum/<int:program_id>/syllabus/add/",
        views.curriculum_syllabus_create,
        name="curriculum_syllabus_create"
    ),

    # 차시 수정
    path(
        "curriculum/syllabus/<int:syllabus_id>/edit/",
        views.curriculum_syllabus_update,
        name="curriculum_syllabus_update"
    ),

    # 차시 삭제
    path(
        "curriculum/syllabus/<int:syllabus_id>/delete/",
        views.curriculum_syllabus_delete,
        name="curriculum_syllabus_delete"
    ),

    path(
        "curriculum/<int:program_id>/syllabus/excel/",
        views.curriculum_syllabus_excel_upload,
        name="curriculum_syllabus_excel_upload",
    ),

    path(
        "curriculum/syllabus/excel/template/",
        views.curriculum_syllabus_excel_template,
        name="curriculum_syllabus_excel_template",
    ),

]
