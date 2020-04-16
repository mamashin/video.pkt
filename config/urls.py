# -*- coding: utf-8 -*-

__author__ = 'Nikolay Mamashin (mamashin@gmail.com)'


from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path
from core.api.viewsets import GetVideo

urlpatterns = [
    path('api/', include('core.api.urls')),
    path('admin/', admin.site.urls),
    re_path(r'^video/', GetVideo.as_view()),
    path('login/', auth_views.LoginView.as_view(template_name='login.html',
                                                redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('core.urls'))
]
