from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', views.userlogin, name='login'),
    path('logout', views.userlogout, name='logout'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('module/<str:moduleName>/',views.module, name='module'),
    path('video/<str:moduleName>/<str:videoId>/', views.video, name='video'),
]