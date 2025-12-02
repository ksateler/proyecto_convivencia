from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil, Curso, Estudiante, Asistencia, Alerta, BitacoraIncidente, AsistenciaSubvencion


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False # Esto al borrar perfil borra el usuario
    verbose_name_plural = 'Perfil de Usuario (Rol)'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,) 


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    # Muestra esto en la lista de cursos
    list_display = ('nombre',)


@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    # Campos en la lista de estudiantes
    list_display = ('id','nombre_completo', 'rut', 'curso')
    list_filter = ('curso',)
    search_fields = ('nombre_completo', 'rut')


@admin.register(Alerta)
class AlertaAdmin(admin.ModelAdmin):
    list_display = ('id','tipo', 'estado', 'curso','creada_por', 'tiempo_creacion')
    list_filter = ('estado', 'tipo', 'creada_por')
    search_fields = ('estudiante_implicado__nombre_completo',)


@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('id','estudiante', 'fecha', 'estado')
    list_filter = ('estado', 'fecha', 'estudiante__curso')
    search_fields = ('estudiante__nombres', 'estudiante__apellidos', 'estudiante__rut')


@admin.register(AsistenciaSubvencion)
class AsistenciaSubvencionAdmin(admin.ModelAdmin):
    list_display = ('id', 'curso', 'fecha', 'tomada_por', 'hora_cierre')
    list_filter = ('fecha', 'curso', 'tomada_por')
    search_fields = ('curso__nombre', 'tomada_por__username')


@admin.register(BitacoraIncidente)
class BitacoraIncidenteAdmin(admin.ModelAdmin):
    list_display = ('id','alerta_asociada', 'estudiante', 'hora_registro')
    list_filter = ('alerta_asociada__tipo', 'estudiante__curso')
    search_fields = ('estudiante__nombres', 'estudiante__apellidos')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

