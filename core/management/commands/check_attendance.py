import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from core.models import Estudiante, Asistencia, Alerta

def count_weekdays(start_date, end_date):
    weekdays = 0
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() < 5:
            weekdays += 1

        current_date += datetime.timedelta(days=1)
    return weekdays

class Command(BaseCommand):
    help = 'Revisa la asistencia de todos los estudiantes y genera alertas si es <= 85%'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando script de revisión de asistencia...'))
        
        try:
            # 1. Obtener fechas clave
            start_date_str = settings.FECHA_INICIO_ANIO_ESCOLAR
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            
            # 2. Calcular total de días hábiles transcurridos
            total_weekdays_elapsed = count_weekdays(start_date, today)
            
            if total_weekdays_elapsed == 0:
                self.stdout.write(self.style.WARNING('No han pasado días hábiles. Saliendo.'))
                return

            self.stdout.write(f"Días hábiles transcurridos: {total_weekdays_elapsed}")

            # 3. Revisar cada estudiante
            estudiantes = Estudiante.objects.all()
            alertas_generadas = 0
            
            for student in estudiantes:
                # 4. Contar asistencias que SÍ cuentan (positivas)
                count_attended = Asistencia.objects.filter(
                    estudiante=student,
                    fecha__range=[start_date, today],
                    estado__in=['presente', 'atrasado']
                ).count()
                
                # 5. Contar asistencias "neutrales" (justificadas)
                count_justified = Asistencia.objects.filter(
                    estudiante=student,
                    fecha__range=[start_date, today],
                    estado__in=['justificado', 'retirado']
                ).count()
                
                # 6. Calcular %
                # El "total" de días son los días hábiles MENOS los justificados
                denominator_adjusted = total_weekdays_elapsed - count_justified
                
                if denominator_adjusted <= 0:
                    # Si solo tiene justificativos, su % es 100%
                    percentage = 100.0
                else:
                    percentage = (count_attended / denominator_adjusted) * 100
                    
                # 7. Comprobar si se debe generar la alerta
                if percentage <= 85.0:
                    
                    # 8. EVITAR DUPLICADOS: Revisamos si ya se creó una alerta HOY
                    already_alerted_today = Alerta.objects.filter(
                        estudiante_implicado=student,
                        tipo='asistencia',
                        tiempo_creacion__date=today
                    ).exists()
                    
                    if not already_alerted_today:
                        # 9. ¡Crear la Alerta!
                        Alerta.objects.create(
                            creada_por=None, # Creada por el "Sistema"
                            tipo='asistencia',
                            estado='pendiente',
                            curso=student.curso,
                            estudiante_implicado=student
                        )
                        alertas_generadas += 1
                        self.stdout.write(self.style.WARNING(
                            f'¡Alerta generada para {student.nombre_completo}! Asistencia: {percentage:.1f}%'
                        ))

            self.stdout.write(self.style.SUCCESS(
                f'Script finalizado. Se generaron {alertas_generadas} alertas nuevas.'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error ejecutando el script: {e}'))