from django.urls import path
from .views import login_view, logout_view, details_view, register_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('details/', details_view, name='details'),
    path('register/', register_view, name='register'),
]