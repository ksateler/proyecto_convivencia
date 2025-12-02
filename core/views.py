from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from .models import Curso, Estudiante, Asistencia, AsistenciaSubvencion, Alerta, BitacoraIncidente
from .forms import BitacoraIncidenteForm
from .resources import BitacoraResource
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import time
from django.core.mail import send_mail
from django.template.loader import render_to_string  # Para emails bonitos
from django.conf import settings


@login_required
def index(request):

    # Esto verifica que el usuario tenga un perfil
    if hasattr(request.user, 'perfil'):
        rol = request.user.perfil.rol

        if rol == 'profesor':
            return redirect('panel_profesor')

        elif rol in ['convivencia', 'utp', 'inspectoria', 'director']:
            return redirect('panel_gestion')

    # 3. Si por alguna razón no tiene rol (ej. el SuperAdmin)
    return render(request, 'core/index.html', {'mensaje': 'Bienvenido Admin (sin rol)'})


def logout_view(request):
    logout(request)
    return redirect('login')


# CONVIVENCIA, UTP, INSPECTORÍA GENERAL Y DIRECTOR
@login_required
def panel_gestion(request):
    rol = request.user.perfil.rol

    alerta = []

    if rol == 'convivencia':
        alerta = ['descompensacion', 'asistencia']
        titulo = "Convivencia Escolar"

    elif rol == 'utp':
        alerta = ['tecnico']
        titulo = "UTP"

    elif rol == 'inspectoria':
        alerta = ['disciplinario', 'salud', 'sos', 'asistencia']
        titulo = "Inspectoría General"

    elif rol == 'director':
        alerta = [choice[0] for choice in Alerta.TIPO_ALERTA]
        titulo = "Dirección"

    else:
        return redirect('index')

    # Muestra las alertas, tipo__in busca las que coincidan y se ordenan de
    # la mas nuevas a las más antiguas
    alertas_area = Alerta.objects.filter(tipo__in=alerta).order_by('-tiempo_creacion')

    # Separación para el panel de vista:
    pendientes = alertas_area.filter(estado='pendiente')
    en_curso = alertas_area.filter(estado='en_curso')
    resueltas = alertas_area.filter(estado='resuelta').select_related(
        'bitacoraincidente',
        'bitacoraincidente__estudiante'
    )
    cursos_para_sos = Curso.objects.all().order_by('nombre')

    context = {
        'titulo': titulo,
        'pendientes': pendientes,
        'en_curso': en_curso,
        'resueltas': resueltas,
        'cursos_para_sos': cursos_para_sos,
    }

    return render(request, 'core/panel_gestion.html', context)


@login_required
def ver_bitacora(request, alerta_id):
    bitacora = get_object_or_404(BitacoraIncidente, alerta_asociada_id=alerta_id)

    rol = request.user.perfil.rol
    tipo_alerta = bitacora.alerta_asociada.tipo

    usuario_autorizado = False
    if rol == 'convivencia' and tipo_alerta == 'descompensacion':
        usuario_autorizado = True
    elif rol == 'utp' and tipo_alerta == 'tecnico':
        usuario_autorizado = True
    elif rol == 'inspectoria' and tipo_alerta in ['disciplinario', 'salud', 'sos']:
        usuario_autorizado = True
    elif rol == 'director':
        usuario_autorizado = True

    if not usuario_autorizado:
        return redirect('panel_gestion')

    context = {
        'bitacora': bitacora
    }

    return render(request, 'core/ver_bitacora.html', context)


# PROFESOR
@login_required
def panel_profesor(request):

    # Esto previene que alguien entre escribiendo la URL directamente
    if not request.user.perfil.rol == 'profesor':
        return redirect('index')

    cursos = Curso.objects.all().order_by('nombre')

    context = {
        'cursos': cursos
    }
    return render(request, 'core/panel_profesor.html', context)


# ASISTENCIA
def tomar_asistencia(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    estudiantes = curso.estudiantes.all().order_by('apellidos', 'nombres')

    # Hora actual
    ahora = timezone.now()
    hoy = ahora.date()
    hora_limite = ahora.time() < time(10, 5)  # Esto significa 10:05 AM

    asistencia_cerrada = AsistenciaSubvencion.objects.filter(
        curso=curso,
        fecha=hoy
    ).exists()

    hora_limite = hora_limite and not asistencia_cerrada

    # Envío asistencia
    if request.method == 'POST':
        for est in estudiantes:
            estado_recibido = request.POST.get(f'asistencia-{est.id}')

            if not estado_recibido:
                continue

            if not hora_limite and estado_recibido in ['ausente', 'atrasado']:
                continue

            datos_a_guardar = {'estado': estado_recibido}

            if estado_recibido == 'retirado':
                datos_a_guardar['hora_retiro'] = ahora.time()
            elif estado_recibido != 'retirado' and hora_limite:
                # en caso de que lo hayan marcado 'retirado' por error
                datos_a_guardar['hora_retiro'] = None

            Asistencia.objects.update_or_create(
                estudiante=est,
                fecha=hoy,
                defaults=datos_a_guardar
            )

    asistencias_guardadas = Asistencia.objects.filter(
        estudiante__in=estudiantes,
        fecha=hoy
    )

    mapa_asistencia_hoy = {
        asistencia.estudiante.id: asistencia.estado
        for asistencia in asistencias_guardadas
    }

    lista_alumnos = []
    for est in estudiantes:
        lista_alumnos.append({
            'estudiante': est,
            'estado_guardado': mapa_asistencia_hoy.get(est.id, None)
        })

    context = {
        'curso': curso,
        'lista_alumnos': lista_alumnos,
        'hora_limite': hora_limite,
    }
    return render(request, 'core/tomar_asistencia.html', context)


@login_required
def asistencia_subvencion(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)
    hoy = timezone.now().date()

    if timezone.now().time() < time(10, 5):
        AsistenciaSubvencion.objects.get_or_create(
            curso=curso,
            fecha=hoy,
            defaults={'cerrada_por': request.user}
        )

    return redirect('tomar_asistencia', curso_id=curso_id)


# Mensaje que ve el profesor al ser aceptada su alerta
@login_required
def check_alertas_profesor(request, curso_id):
    alertas_en_curso = Alerta.objects.filter(
        creada_por=request.user,
        curso_id=curso_id,
        estado='en_curso'
    ).select_related('atendida_por')

    datos_aterta = []

    for alerta in alertas_en_curso:
        hora_utc = alerta.tiempo_aceptacion
        hora_local = timezone.localtime(hora_utc)
        hora_formateada = hora_local.strftime('%H:%M')

        datos_aterta.append({
            'tipo': alerta.get_tipo_display(),
            'atendida_por': alerta.atendida_por.username,
            'tiempo_aceptacion': hora_formateada,
        })

    return JsonResponse({'alertas': datos_aterta})


# ALERTA
@login_required
@require_POST
def crear_alerta(request):

    tipo_alerta = request.POST.get('tipo')
    curso_id = request.POST.get('curso_id')
    descripcion_profesor = request.POST.get('descripcion', None)  # Si está vacío es None

    tipos_validos = [choice[0] for choice in Alerta.TIPO_ALERTA]
    if tipo_alerta not in tipos_validos:
        if request.user.perfil.rol == 'profesor':
            return redirect('tomar_asistencia', curso_id=curso_id)
        else:
            return redirect('panel_gestion')

    curso_obj = None
    # Validar curso
    if curso_id:
        try:
            curso_obj = Curso.objects.get(id=curso_id)
        except Curso.DoesNotExist:
            return redirect('panel_profesor')
    else:
        if tipo_alerta in ['sos', 'tecnico', 'descompensacion', 'disciplinario', 'salud']:
            return redirect('panel_gestion')
    # Si no hay curso no se crea la alerta

    Alerta.objects.create(
        creada_por=request.user,
        tipo=tipo_alerta,
        curso=curso_obj,
        descripcion_profesor=descripcion_profesor,
    )

    return redirect('tomar_asistencia', curso_id=curso_id)


@login_required
def acudir_alerta(request, alerta_id):
    alerta = get_object_or_404(Alerta, id=alerta_id)

    # Se verifica que el usuario pertenezca a alguno de los roles
    if request.user.perfil.rol in ['convivencia', 'utp', 'inspectoria', 'director']:

        if alerta.estado == 'pendiente':
            alerta.estado = 'en_curso'
            alerta.atendida_por = request.user  # Se asigna al empleado logueado
            alerta.tiempo_aceptacion = timezone.now()  # Se guarda la hora
            alerta.save()

            # (Aquí es donde, en el futuro, se enviaría
            # la señal de WebSocket o la notificación push)

    return redirect('panel_gestion')


@login_required
def resolver_alerta(request, alerta_id):
    alerta = get_object_or_404(Alerta, id=alerta_id)

    if alerta.atendida_por != request.user and request.user.perfil.rol != 'director':
        # Acá puede ir un mensaje de "no permitido o no autorizado"
        return redirect('panel_gestion')

    curso = alerta.curso
    estudiantes_del_curso = Estudiante.objects.filter(curso=curso).order_by('apellidos')

    if request.method == 'POST':
        form = BitacoraIncidenteForm(request.POST, curso=curso, alerta=alerta)

        if form.is_valid():
            bitacora = form.save(commit=False)
            bitacora.alerta_asociada = alerta

            if not form.cleaned_data.get('estudiante'):
                if alerta.estudiante_implicado:
                    bitacora.estudiante = alerta.estudiante_implicado

            bitacora.save()

            alerta.estado = 'resuelta'
            alerta.save()

            # EMAIL CON INFO PARA EL ENCARGADO QUE ATENDIÓ EL INCIDENTE
            try:
                context_email = {
                    'bitacora': bitacora,
                    'alerta': alerta,
                    'encargado': request.user,
                }
                asunto = f"Copia de Respaldo: Alerta Resuelta #{alerta.id} - {alerta.get_tipo_display()}"
                mensaje_texto = f"""
                Hola {request.user.first_name or request.user.username},

                Se ha generado una copia de respaldo de la alerta que resolviste en el sistema de Alertas Escolares.

                DETALLES:
                - Alerta ID: {alerta.id}
                - Tipo: {alerta.get_tipo_display()}
                - Curso: {alerta.curso.nombre}
                - Reportó: {alerta.creada_por.username or 'Sistema'}
                - Resuelta por: {request.user.username}
                """

                if bitacora.estudiante:
                    mensaje_texto += f"""
                BITÁCORA:
                - Estudiante: {bitacora.estudiante.nombre_completo}
                - Apoderado: {bitacora.estudiante.nombre_apoderado or 'N/A'}
                - Fono Apoderado: {bitacora.estudiante.telefono_apoderado or 'N/A'}
                - Email Apoderado: {bitacora.estudiante.email_apoderado or 'N/A'}
                """
                else:
                    mensaje_texto += """
                - Estudiante: N/A 
                """
            
                mensaje_texto += f"""

                - Descripción del suceso: {bitacora.descripcion_suceso}

                Este correo es una copia de respaldo automática para tus registros.
                No es necesario responder a este mensaje.
                """

                # Envío del mail
                send_mail(
                    asunto,
                    mensaje_texto,
                    settings.DEFAULT_FROM_EMAIL, # Email desde por ejemplo sistema@colegio.cl
                    [request.user.email],       # Email para el encargado
                    fail_silently=False,
                )

            except Exception as e:
                print(f"Error al enviar email: {e}")

            return redirect('panel_gestion')

    else:
        form = BitacoraIncidenteForm(curso=curso, alerta=alerta)

    context = {
        'form': form,
        'alerta': alerta,
        'curso': curso,
        'estudiantes_del_curso': estudiantes_del_curso,
    }

    return render(request, 'core/resolver_alerta.html', context)


@login_required
def check_alertas_gestion(request):

    rol = request.user.perfil.rol
    tipos_de_alerta_a_mostrar = []

    if rol == 'convivencia':
        tipos_de_alerta_a_mostrar = ['descompensacion', 'asistencia']
    elif rol == 'utp':
        tipos_de_alerta_a_mostrar = ['tecnico']
    elif rol == 'inspectoria':
        tipos_de_alerta_a_mostrar = ['disciplinario', 'salud', 'sos', 'asistencia']
    elif rol == 'director':
        tipos_de_alerta_a_mostrar = [choice[0]  for choice in Alerta.TIPO_ALERTA]
    else:
        # Si no es un rol de gestión no devuelve nada
        return JsonResponse({'error': 'No autorizado'}, status=403)

    conteo_pendientes = Alerta.objects.filter(
        tipo__in=tipos_de_alerta_a_mostrar,
        estado='pendiente'
    ).count()

    return JsonResponse({'conteo_pendientes': conteo_pendientes})


@login_required
def exportar_bitacoras_excel(request):
    # Por ahora solo el director puede descargar reportes
    if not request.user.perfil.rol == 'director':
        return redirect('index')

    bitacora_resource = BitacoraResource()

    queryset = BitacoraIncidente.objects.all()

    dataset = bitacora_resource.export(queryset)

    response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reporte_bitacoras.xlsx"'

    return response
