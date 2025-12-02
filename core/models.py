from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


# ESTE MODELO TOMA EL USUARIO YA DEFINIDDO DE LA BD DE DJANGO Y ASIGNA ROLES
class Perfil(models.Model):
    ROLES = [
        ('profesor', 'Profesor'),
        ('convivencia', 'Convivencia Escolar'),
        ('utp', 'UTP'),
        ('inspectoria', 'Inspectoría General'),
        ('director', 'Director'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES)
    rut = models.CharField(max_length=12, unique=True, null=True, blank=True, verbose_name="RUT (sin puntos, con guión)")

    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"


# MODELOS DEL COLEGIO
class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    profesores = models.ManyToManyField(
        User,
        related_name="cursos",
        blank=True,
        limit_choices_to={'perfil__rol': 'profesor'}
    )

    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse("tomar_asistencia", kwargs={"curso_id": self.id})
    


class Estudiante(models.Model):
    nombres = models.CharField(max_length=255)
    apellidos = models.CharField(max_length=255)
    rut = models.CharField(max_length=12, unique=True)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="estudiantes")

    nombre_apoderado = models.CharField(max_length=255, blank=True, null=True)
    telefono_apoderado = models.CharField(max_length=15, blank=True, null=True)
    email_apoderado = models.EmailField(blank=True, null=True)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    def __str__(self):
        nombre_curso = self.curso.nombre if self.curso else "Sin Curso"
        return f"{self.nombre_completo} - {nombre_curso}"
    
    def get_absolute_url(self):
        return reverse("perfil_estudiante", kwargs={"pk": self.id})
    


# MODELO ASISTECIA
class Asistencia(models.Model):
    ESTADOS = [
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('atrasado', 'Atrasado'),
        ('justificado', 'Justificado'),
        ('retirado', 'Retirado'),
    ]
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    estado = models.CharField(max_length=15, choices=ESTADOS)
    hora_retiro = models.TextField(null=True, blank=True)

    # Esto evita que se duplique la asistencia de un alumno
    class Meta:
        unique_together = ('estudiante', 'fecha')

    def __str__(self):
        return f"{self.estudiante.nombre_completo} - {self.fecha} - {self.get_estado_display()}"

# Asistecia del primer bloque
class AsistenciaSubvencion(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    tomada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    hora_cierre = models.DateTimeField(auto_now_add=True)

    class Meta:
        # solo se puede cerrar una vez por curso y día
        unique_together = ('curso', 'fecha')

    def __str__(self):
        return f"Cierre de {self.curso.nombre} - {self.fecha}"

# MODELO DE ALERTAS
class Alerta(models.Model):
    TIPO_ALERTA = [
        ('descompensacion', 'Descompensación'),
        ('tecnico', 'Apoyo Técnico'),
        ('disciplinario', 'Disciplinario'),
        ('salud', 'Salud'),
        ('sos', 'SOS'),
        ('asistencia', 'Asistencia menor al 85%'),
    ]
    ESTADO_ALERTA = [
        ('pendiente', 'Pendiente'),
        ('en_curso', 'En Curso'),
        ('resuelta', 'Resuelta'),
    ]
    creada_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="alertas_creadas")
    tiempo_creacion = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TIPO_ALERTA)
    estado = models.CharField(max_length=15, choices=ESTADO_ALERTA, default='pendiente')
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, null=True)
    # Campo para manejar alertas de Baja Asistencia
    estudiante_implicado = models.ForeignKey(Estudiante, on_delete=models.SET_NULL, null=True, blank=True)
    atendida_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="alertas_atendidas")
    descripcion_profesor = models.TextField(blank=True, null=True, verbose_name="Descripción del profesor")
    # Esto se llena cuando alguien la toma
    tiempo_aceptacion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        curso_nombre = self.curso.nombre if self.curso else "Curso no especificado"
        return f"Alerta {self.get_tipo_display()} en {curso_nombre} ({self.estado})"

    def get_absolute_url(self):

        if self.estado == 'en_curso':
            return reverse('resolver_alerta', kwargs={'alerta_id': self.id})
        
        elif self.estado == 'resuelta':
            return reverse('ver_bitacora', kwargs={'alerta_id': self.id})
        
        else:
            return reverse('panel_gestion')


# MODELO DE FORMULAIRO
class BitacoraIncidente(models.Model):
    SUBTIPO = [
        ('emocional', 'Emocional'),
        ('convivencia', 'Convivencia'),
    ]
    alerta_asociada = models.OneToOneField(Alerta, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.SET_NULL, null=True, blank=True)
    subtipo_descompensacion = models.CharField(
        max_length=20, 
        choices=SUBTIPO, 
        null=True, 
        blank=True,
        verbose_name="Subtipo de Descompensación"
    )
    descripcion_suceso = models.TextField(verbose_name="Descripción de lo sucedido")
    hora_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        alerta = self.alerta_asociada
        estudiante_nombre = self.estudiante.nombre_completo if self.estudiante else "N/A"
        return f"Bitácora de Alerta #{alerta.id} {alerta.get_tipo_display()} -  {estudiante_nombre}"

    def get_absolute_url(self):
        return reverse("ver_bitacora", kwargs={"alerta_id": self.id})
    