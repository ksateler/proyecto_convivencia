from django import forms
from .models import BitacoraIncidente, Estudiante, Alerta


class BitacoraIncidenteForm(forms.ModelForm):

    estudiante = forms.ModelChoiceField(
        queryset=Estudiante.objects.none(),
        required=True, 
        label='Estudiante involucrado'
    )

    class Meta:
        model = BitacoraIncidente
        fields = ['estudiante', 'subtipo_descompensacion', 'descripcion_suceso']
        widgets = {
            'descripcion_suceso': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe brevemente lo sucedido y las acciones tomadas.'}),
            'subtipo_descompensacion': forms.RadioSelect,
        }

    # Filtra por curso y solo muestra los que correspondan a este
    def __init__(self, *args, **kwargs):
        curso = kwargs.pop('curso', None)
        alerta = kwargs.pop('alerta', None) 

        super().__init__(*args, **kwargs)

        campo_estudiante = self.fields['estudiante']
        campo_subtipo = self.fields.get('subtipo_descompensacion')
        campo_descripcion = self.fields.get('descripcion_suceso')

        if alerta and alerta.tipo == 'asistencia':
            # Se oculta la lista para seleccionar estudiante(ya está por defecto)
            if campo_estudiante:
                campo_estudiante.required = False
                campo_estudiante.widget = forms.HiddenInput()
            
            # Se oculta sub tipo de descompensacón
            if campo_subtipo:
                campo_subtipo.required = False
                campo_subtipo.widget = forms.HiddenInput()

            if campo_descripcion:
                campo_descripcion.label = "Medidas Tomadas"
                campo_descripcion.widget.attrs['placeholder'] = 'Descripción'
        
        # Si la alerta es de Apoyo Técnico NO es obligatorio
        elif alerta and alerta.tipo == 'tecnico':
            if campo_estudiante:
                campo_estudiante.required = False
                campo_estudiante.widget = forms.HiddenInput()
            
            if campo_subtipo:
                campo_subtipo.required = False
                campo_subtipo.widget = forms.HiddenInput()

        elif alerta and alerta.tipo == 'descompensacion':
            # Se despliega selección de estudiante y filtra por curso
            if campo_estudiante:
                campo_estudiante.required = True
                if curso:
                    campo_estudiante.queryset = Estudiante.objects.filter(
                        curso=curso
                    ).order_by('apellidos', 'nombres')
            
            # Acá como es descompensación pide un subtipo(emocional/convivencia)
            if campo_subtipo:
                campo_subtipo.required = True
                campo_subtipo.label = "Indique el subtipo de descompensación"
        
        # Salud y Disciplinario
        else:
            if campo_estudiante:
                campo_estudiante.required = True
                if curso:
                    campo_estudiante.queryset = Estudiante.objects.filter(
                        curso=curso
                    ).order_by('apellidos', 'nombres')
            
            if campo_subtipo:
                campo_subtipo.required = False
                campo_subtipo.widget = forms.HiddenInput()