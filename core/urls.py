from django.urls import path
from . import views

urlpatterns = [
    # Vista index redirige por rol
    path('', views.index, name='index'),

    # Vistas Profesor
    path('panel-profesor/', views.panel_profesor, name='panel_profesor'),
    path('crear-alerta/', views.crear_alerta, name='crear_alerta'),
    path('curso/<int:curso_id>/', views.tomar_asistencia, name='tomar_asistencia'),
    path('curso/<int:curso_id>/asistencia_subvencion/', views.asistencia_subvencion, name='asistencia_subvencion'),
    path('api/check-alertas-profesor/<int:curso_id>/', views.check_alertas_profesor, name='check_alertas_profesor'),

    # Vistas Convivencia, Inspectoría, UTP
    path('panel-gestion/', views.panel_gestion, name='panel_gestion'),
    path('alerta/<int:alerta_id>/acudir/', views.acudir_alerta, name='acudir_alerta'),
    path('alerta/<int:alerta_id>/resolver/', views.resolver_alerta, name='resolver_alerta'),
    path('api/check-alertas-gestion/', views.check_alertas_gestion, name='check_alertas_gestion'),
    path('alerta/<int:alerta_id>/bitacora/', views.ver_bitacora, name='ver_bitacora'),
    
    # Exclusivo vista Director
    path('exportar/bitacoras/', views.exportar_bitacoras_excel, name='exportar_bitacoras'),
]
