
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
]