# ESTE ARCHIVO TRABAJA CON LA LIBRERÍA QUE EXPROTA LOS
# DATOS EN EXCEL

from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import BitacoraIncidente, User, Estudiante, Alerta

class BitacoraResource(resources.ModelResource):
    # Esto sirve para ir sacando la info, en este caso el tipo de alerta
    tipo_alerta = fields.Field(column_name= 'Tipo alerta',)

    # Rut del estudiante
    rut_estudiante = fields.Field(
        column_name='RUT Estudiante',
        attribute='estudiante', 
        widget=ForeignKeyWidget(Estudiante, 'rut')
    )

    # Nombre del estudiante
    nombre_estudiante = fields.Field(
        column_name='Nombre Estudiante',
        attribute='estudiante',
        widget=ForeignKeyWidget(Estudiante, 'nombre_completo')
    )

    # Curso del estudiante
    curso_estudiante = fields.Field(
        column_name='Curso',
        attribute='estudiante',
        widget=ForeignKeyWidget(Estudiante, 'curso__nombre')
    )

    # Encargado que resolvió la alerta
    nombre_encargado = fields.Field(column_name='Encargado',)

    rol_encargado = fields.Field(column_name='Rol Encargado')

    #Profesor que reportó
    reporto_profesor = fields.Field(column_name='Reportado por',)


    # Aquí decimos CÓMO rellenar los campos que creamos
    def dehydrate_tipo_alerta(self, bitacora):
        return bitacora.alerta_asociada.get_tipo_display()


    def dehydrate_nombre_encargado(self, bitacora):
        user = bitacora.alerta_asociada.atendida_por
        if user:
            return user.get_full_name() or user.username
        return "N/A" # Si es que no hay encargado
    

    def dehydrate_rol_encargado(self, bitacora):
        user = bitacora.alerta_asociada.atendida_por
        if user and hasattr(user, 'perfil'):
            return user.perfil.get_rol_display()
        elif user:
            return "Admin/Sin Rol" # Si el usuario no tiene perfil
        return "N/A" # Si no hay usuario


    def dehydrate_reporto_profesor(self, bitacora):
        user = bitacora.alerta_asociada.creada_por
        if user:
            return user.get_full_name() or user.username
        # Si creada_por es None como las alertas de asistencia, pone Sistema
        return "Sistema"

    class Meta:
        model = BitacoraIncidente

        fields = (
            'id',
            'hora_registro',
            'descripcion_suceso',
            'subtipo_descompensacion',
            'tipo_alerta',        
            'rut_estudiante',     
            'nombre_estudiante',  
            'curso_estudiante',
            'nombre_encargado',  
            'rol_encargado', 
            'reporto_profesor',
        )

        export_order =(
            'id',
            'hora_registro',
            'rut_estudiante',
            'nombre_estudiante',
            'curso_estudiante',
            'tipo_alerta',
            'subtipo_descompensacion',
            'nombre_encargado',
            'rol_encargado',
            'reporto_profesor', 
            'descripcion_suceso',
        )

        # No exporta campos que no hayamos definido
        use_natural_foreign_keys = False
