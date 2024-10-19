from django.urls import path
from . import views

urlpatterns = [
    ############## CARS ###################
    path('', views.dash, name='home'),
    path('login/', views.login_view, name='login'),  # Route for login
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),  # Route for signup
    path('signup-success/', views.signup_success, name='signup_success'),  # Route for signup
    path('member-dashboard/', views.members, name='members'),  # Route for signup
    path('submit-fee/', views.submit_fees, name='submit_fee'),
    path('renew-membership/', views.renew_membership, name='renew_membership'),
    path('member/<int:member_id>/', views.view_member, name='view_member'),
    path('toggle-member-status/<int:member_id>/', views.toggle_member_status, name='toggle_member_status'),
    path('delete-member/<int:member_id>/', views.delete_member, name='delete_member'),
    path('tehsils-map/', views.tehsils_map, name='tehsils_map'),
    path('pending-renewal-requests/', views.pending_requests, name='pending_requests'),
    path('renewal-request/<int:request_id>/', views.view_change_request, name='view_change_request'),
    path('get-tehsil/<int:district_id>/', views.get_tehsils, name='get_tehsils'),
    path('<int:order_id>/invoice/', views.generate_receipt_view, name='generate_receipt'),
    path('<int:order_id>/members-detail/', views.generate_member_detail, name='generate_member_detail'),

]