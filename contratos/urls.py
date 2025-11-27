from django.urls import path

from .views import generar_contrato

app_name = "contratos"

urlpatterns = [
    path("", generar_contrato, name="generar_contrato"),
]
