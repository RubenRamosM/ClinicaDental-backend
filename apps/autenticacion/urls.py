"""
URLs para autenticación.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('registro/', views.RegistroView.as_view(), name='registro'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('recuperar-password/', views.RecuperarPasswordView.as_view(), name='recuperar-password'),
    path('cambiar-password/', views.CambiarPasswordView.as_view(), name='cambiar-password'),
    path('verificar-token/', views.VerificarTokenView.as_view(), name='verificar-token'),
    path('perfil/', views.PerfilView.as_view(), name='perfil'),
]
