from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import Perfil

# esto permite que el usuario se loguee con el rut
class RUTAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Busca un perfil con el rut que se ingresó
        try:
            perfil = Perfil.objects.get(rut=username)

        except Perfil.DoesNotExist:
            return None
        except Exception as e:
            print(f"Error de autenticación: {e}")
            return None
        
        user = perfil.usuario

        # Verificación de contraseña
        if user.check_password(password):
            return user
        
        return None
    
    # Django pide el ID para validar, y no es recomendable usar el rut como PK
    # por eso todo esto
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None