
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
]