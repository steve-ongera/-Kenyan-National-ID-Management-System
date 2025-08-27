
from django.urls import path
from . import views


urlpatterns = [
    # Authentication URLs
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard redirect
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    
    # Dashboard URLs for different user types
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('chief-dashboard/', views.chief_dashboard, name='chief_dashboard'),
    path('chief-staff-dashboard/', views.chief_dashboard, name='chief_staff_dashboard'),
    path('do-dashboard/', views.do_dashboard, name='do_dashboard'),
    path('do-staff-dashboard/', views.do_dashboard, name='do_staff_dashboard'),
    path('huduma-dashboard/', views.do_dashboard, name='huduma_dashboard'),
    path('citizen-dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    
    # API endpoints for dashboard data
    path('api/dashboard/stats/', views.dashboard_api_stats, name='dashboard_api_stats'),
    path('api/dashboard/applications-trend/', views.dashboard_api_applications_trend, name='dashboard_api_applications_trend'),

     path('applications/', views.id_applications_list, name='applications_list'),
    path('create/applications/', views.id_application_create, name='applications_create'),
    path('<uuid:application_id>/', views.id_application_detail, name='applications_detail'),
    path('<uuid:application_id>/update/', views.id_application_update, name='applications_update'),
    path('<uuid:application_id>/delete/', views.id_application_delete, name='applications_delete'),
    
    # API endpoints
    path('api/<uuid:application_id>/detail/', views.id_application_api_detail, name='applications_api_detail'),
    
    # Location API endpoints for cascading dropdowns
    path('api/counties/<int:county_id>/sub-counties/', views.get_sub_counties, name='get_sub_counties'),
    path('api/sub-counties/<int:sub_county_id>/divisions/', views.get_divisions, name='get_divisions'),
    path('api/divisions/<int:division_id>/locations/', views.get_locations, name='get_locations'),
    path('api/locations/<int:location_id>/sub-locations/', views.get_sub_locations, name='get_sub_locations'),
    path('api/sub-locations/<int:sub_location_id>/villages/', views.get_villages, name='get_villages'),

    # Birth Certificates
    path('birth-certificates/', views.birth_certificates_list, name='birth_certificates_list'),
    path('birth-certificates/create/', views.birth_certificate_create, name='birth_certificate_create'),
    path('birth-certificates/<str:certificate_number>/', views.birth_certificate_detail, name='birth_certificate_detail'),
    path('birth-certificates/<str:certificate_number>/update/', views.birth_certificate_update, name='birth_certificate_update'),
    path('birth-certificates/<str:certificate_number>/delete/', views.birth_certificate_delete, name='birth_certificate_delete'),

    # List and dashboard
    path('national_id/', views.national_id_list, name='national_id_list'),
    path('statistics/', views.national_id_statistics, name='national_id_statistics'),
    
    path('national_id/create/', views.national_id_create, name='national_id_create'),
    path('national_id/<str:id_number>/', views.national_id_detail, name='national_id_detail'),
    path('national_id/<str:id_number>/edit/', views.national_id_update, name='national_id_update'),
    path('national_id/<str:id_number>/delete/', views.national_id_delete, name='national_id_delete'),
    
    # Status management
    path('<str:id_number>/mark-collected/', views.national_id_mark_collected, name='national_id_mark_collected'),
    path('<str:id_number>/mark-printed/', views.national_id_mark_printed, name='national_id_mark_printed'),
    path('<str:id_number>/mark-dispatched/', views.national_id_mark_dispatched, name='national_id_mark_dispatched'),
    
    # AJAX endpoints
    path('ajax/sub-counties/', views.ajax_sub_counties, name='ajax_sub_counties'),
]