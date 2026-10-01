"""
URL configuration for meu_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from nutricao import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='nutricao/login.html'), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('painel/', views.lista_refeicoes, name='painel'),
    path('cadastro/', views.cadastrar_usuario, name='cadastro'),
    path('adicionar/', views.adicionar_refeicao_ia, name='adicionar_ia'),
    path('definir-metas/',views.definir_metas, name='definir_metas'),
    path('historico/', views.historico, name="historico")
]
