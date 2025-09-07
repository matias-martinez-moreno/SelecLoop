# ===== COMANDO DE GESTIÓN: CREAR PERFILES DE USUARIO =====
# Este archivo define un comando personalizado de Django para crear perfiles de usuario
# Se ejecuta desde la línea de comandos con: python manage.py create_user_profiles

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile

class Command(BaseCommand):
    """
    Comando personalizado para crear perfiles de usuario para usuarios existentes.
    
    Este comando es útil cuando:
    - Se migra una base de datos existente
    - Se tienen usuarios sin perfiles
    - Se necesita crear perfiles en lote
    
    Uso:
        python manage.py create_user_profiles
        
    Opciones:
        --force: Forzar la creación incluso si ya existen perfiles
        --role: Especificar el rol por defecto (candidate, company_rep, staff)
    """
    
    # ===== CONFIGURACIÓN DEL COMANDO =====
    help = 'Crea perfiles de usuario para usuarios que no los tienen'
    
    def add_arguments(self, parser):
        """
        Define los argumentos opcionales del comando.
        
        Args:
            parser: Parser de argumentos de Django
        """
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la creación incluso si ya existen perfiles',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['candidate', 'company_rep', 'staff'],
            default='candidate',
            help='Rol por defecto para los nuevos perfiles',
        )
    
    def handle(self, *args, **options):
        """
        Método principal que se ejecuta cuando se llama al comando.
        
        Args:
            *args: Argumentos posicionales
            **options: Opciones del comando
        """
        # ===== OBTENER OPCIONES =====
        force = options['force']
        default_role = options['role']
        
        # ===== MOSTRAR INFORMACIÓN INICIAL =====
        self.stdout.write(
            self.style.SUCCESS(
                f'Iniciando creación de perfiles de usuario con rol por defecto: {default_role}'
            )
        )
        
        # ===== OBTENER USUARIOS SIN PERFIL =====
        users_without_profile = User.objects.filter(profile__isnull=True)
        total_users = users_without_profile.count()
        
        if total_users == 0:
            self.stdout.write(
                self.style.WARNING('No hay usuarios sin perfil.')
            )
            return
        
        self.stdout.write(
            f'Encontrados {total_users} usuarios sin perfil.'
        )
        
        # ===== CREAR PERFILES =====
        created_count = 0
        skipped_count = 0
        
        for user in users_without_profile:
            try:
                # Verificar si ya existe un perfil (por si acaso)
                if hasattr(user, 'profile') and user.profile:
                    if force:
                        # Forzar recreación del perfil
                        user.profile.delete()
                        self.stdout.write(f'Perfil eliminado para {user.username}')
                    else:
                        # Saltar usuario con perfil existente
                        skipped_count += 1
                        continue
                
                # Crear nuevo perfil
                profile = UserProfile.objects.create(
                    user=user,
                    role=default_role
                )
                
                created_count += 1
                self.stdout.write(
                    f'✓ Perfil creado para {user.username} con rol {default_role}'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error creando perfil para {user.username}: {str(e)}'
                    )
                )
        
        # ===== MOSTRAR RESUMEN =====
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RESUMEN DE LA OPERACIÓN')
        self.stdout.write('='*50)
        self.stdout.write(f'Total de usuarios procesados: {total_users}')
        self.stdout.write(f'Perfiles creados: {created_count}')
        self.stdout.write(f'Usuarios omitidos: {skipped_count}')
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Se crearon exitosamente {created_count} perfiles de usuario.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠ No se crearon nuevos perfiles.'
                )
            )
