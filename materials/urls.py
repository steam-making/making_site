from django.urls import path
from . import views

urlpatterns = [
    path('', views.material_list, name='material_list'),
    path('create/', views.material_create, name='material_create'),
    path('materials/<int:pk>/edit/', views.material_edit, name='material_edit'),
    path('materials/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/edit/', views.vendor_edit, name='vendor_edit'),
    path('vendors/<int:pk>/update/', views.vendor_update, name='vendor_update'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),
    path('materials/upload/', views.material_bulk_upload, name='material_bulk_upload'),
    path('materials/template/download/', views.download_material_template, name='download_material_template'),
    path("materials/<int:pk>/history/", views.material_history, name="material_history"),
    
    path('types/', views.vendor_type_list, name='vendor_type_list'),
    path('types/create/', views.vendor_type_create, name='vendor_type_create'),
    path('types/<int:pk>/update/', views.vendor_type_update, name='vendor_type_update'),
    path('types/<int:pk>/delete/', views.vendor_type_delete, name='vendor_type_delete'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/new/', views.create_order, name='create_order'),
    path('orders/receive/<int:order_id>/', views.receive_order, name='receive_order'),
    path('orders/item/receive/<int:item_id>/', views.receive_material_item, name='receive_material_item'),
    
    # 각 항목 수정 및 삭제
    path('orders/item/<int:item_id>/edit/', views.edit_material_item, name='edit_material_item'),
    path('orders/item/<int:item_id>/delete/', views.delete_material_item, name='delete_material_item'),
    
    path('releases/', views.release_list, name='release_list'),
    path('releases/new/', views.create_release, name='create_release'),  
    path('release/<int:release_id>/toggle-payment/', views.toggle_payment_status, name='toggle_payment_status'),
    path('orders/item/release/<int:item_id>/', views.release_material_item, name='release_material_item'),
    path('estimate/<int:institution_id>/<str:order_month>/', views.generate_estimate, name='generate_estimate'),
    path('toggle-payment/<int:institution_id>/<str:order_month>/', views.toggle_payment_status, name='toggle_payment_status'),
    
    # 2단계 플로우
    path('releases/estimate/<int:institution_id>/<str:order_month>/preview/', views.estimate_preview, name='estimate_preview'),
    path('releases/estimate/<int:institution_id>/<str:order_month>/pdf/', views.estimate_pdf, name='estimate_pdf'),                 # PDF 미리보기/다운로드
    path('releases/estimate/<int:institution_id>/<str:order_month>/send/', views.estimate_send, name='estimate_send'),               # 이메일 발송 + redirect


    path('item/<int:item_id>/release/', views.release_material_item, name='release_material_item'),
    path('item/<int:item_id>/unrelease/', views.unrelease_material_item, name='unrelease_material_item'),
    
    path('releases/item/<int:item_id>/edit/', views.edit_release_item, name='edit_release_item'),
    path('releases/item/<int:item_id>/delete/', views.delete_release_item, name='delete_release_item'),
    path('releases/group/<int:institution_id>/<str:order_month>/delete/', views.delete_release_group, name='delete_release_group'),
    
    
    path('materials/bulk_delete/', views.material_bulk_delete, name='material_bulk_delete'),
    path("orders/item/<int:item_id>/toggle_payment/", views.toggle_payment_item, name="toggle_payment_item"),
    
    # ✅ 주문 그룹 단위 (날짜별)
    path("orders/group/<str:grouper>/toggle_payment/", views.toggle_payment_group, name="toggle_payment_group"),
    path("orders/group/<str:grouper>/receive/", views.receive_group, name="receive_group"),
    path("orders/group/<str:grouper>/delete/", views.delete_group_orders, name="delete_group_orders"),
    
    path('groups/<str:date_str>/<int:vendor_type_id>/<int:vendor_id>/toggle-payment/',
         views.toggle_payment_vendor_group, name='toggle_payment_vendor_group'),
    path('groups/<str:date_str>/<int:vendor_type_id>/<int:vendor_id>/toggle-receive/',
         views.toggle_receive_vendor_group, name='toggle_receive_vendor_group'),
    path('groups/<str:date_str>/<int:vendor_type_id>/<int:vendor_id>/delete/',
         views.delete_vendor_group_orders, name='delete_vendor_group_orders'),
    
    # 세금계산서 발행 URL
    path("releases/tax-invoice/<int:institution_id>/<str:order_month>/", views.tax_invoice_issue, name="tax_invoice_issue"),
    # 교구재 순서 저장
    path("materials/reorder/", views.material_reorder, name="reorder_materials"), 
    
    #교구재 반납
    path("release/<int:item_id>/return/", views.return_release_item, name="return_release_item"),
    
    # ✅ 강사용 반납 목록
    path("returns/", views.return_list, name="return_list"),
    path("release/payment/<int:institution_id>/<str:order_month>/",views.set_payment_date,name="set_payment_date",),
]

