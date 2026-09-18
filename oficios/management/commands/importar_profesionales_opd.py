import os
import re
import unicodedata
import openpyxl
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from oficios.models import Institucion
from core.models import UsuarioPerfil

User = get_user_model()

EXCEL_PERSONAL_PATH = r'\\snfserver2\Informatica\notas de pedido\capacitaciones_GDE\personal_OPD_limpio.xlsx'
DEFAULT_PASSWORD = 'opd.usuario.2026'

MAPA_OPD_A_BD = {
    'Abra Pampa': 'O.P.D.N.N.A. ABRA PAMPA',
    'Aguas Calientes': 'O.P.D.N.N.A. AGUAS CALIENTES',
    'Alto Comedero I - Guillermo Snopek': 'O.P.D.N.N.A. ALTO COMEDERO 1',
    'Alto Comedero II - San Antonio': 'O.P.D.N.N.A. ALTO COMEDERO 2',
    'Alto Comedero III - Tupac Amaru': 'O.P.D.N.N.A. ALTO COMEDERO 3',
    'Calilegua': 'O.P.D.N.N.A. CALILEGUA',
    'Centro Integral San Pedro': 'O.P.D.N.N.A. SAN PEDRO',
    'Centro de Atención Integral Humahuaca': 'O.P.D.N.N.A. HUMAHUACA',
    'Chijra': 'O.P.D.N.N.A. CHIJRA',
    'Coronel Arias': 'O.P.D.N.N.A. CORONEL ARIAS',
    'Cuyaya': 'O.P.D.N.N.A. CUYAYA',
    'El Carmen': 'O.P.D.N.N.A. EL CARMEN',
    'Fraile Pintado': 'O.P.D.N.N.A. FRAILE PINTADO',
    'La Esperanza': 'O.P.D.N.N.A. LA ESPERANZA',
    'La Mendieta': 'O.P.D.N.N.A. LA MENDIETA',
    'La Quiaca': 'O.P.D.N.N.A. LA QUIACA',
    'Libertador Gral. San Martín': 'O.P.D.N.N.A. LIBERTADOR GRAL SAN MARTIN',
    'Maimará': 'O.P.D.N.N.A. MAIMARA',
    'Monterrico': 'O.P.D.N.N.A. MONTERRICO',
    'Palma Sola': 'O.P.D.N.N.A. PALMA SOLA',
    'Palpalá': 'O.P.D.N.N.A. PALPALA',
    'Perico': 'O.P.D.N.N.A. PERICO',
    'Puesto Viejo': 'O.P.D.N.N.A. PUESTO VIEJO',
    'Rodeito': 'O.P.D.N.N.A. RODEITO',
    'San Antonio': 'O.P.D.N.N.A. SAN ANTONIO',
    'San Pedrito - Sol Para Todos': 'O.P.D.N.N.A. SAN PEDRITO',
    'Santa Clara': 'O.P.D.N.N.A. SANTA CLARA',
    'Tilcara': 'O.P.D.N.N.A. TILCARA',
    'Yala': 'O.P.D.N.N.A. YALA',
    'Yuto': 'O.P.D.N.N.A. YUTO'
}

def generar_username_base(nombre, apellido):
    n = unicodedata.normalize('NFKD', str(nombre or '')).encode('ASCII', 'ignore').decode('utf-8')
    a = unicodedata.normalize('NFKD', str(apellido or '')).encode('ASCII', 'ignore').decode('utf-8')
    n_tok = re.sub(r'[^A-Z]', ' ', n.upper()).split()
    a_tok = re.sub(r'[^A-Z]', ' ', a.upper()).split()
    ini = n_tok[0][0].lower() if n_tok else 'u'
    ape = a_tok[0].lower() if a_tok else 'usuario'
    return f"{ini}{ape}"

class Command(BaseCommand):
    help = 'Importa la nómina de profesionales desde personal_OPD_limpio.xlsx asignando su OPD oficial y credenciales genéricas.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simular sin crear usuarios en base de datos.')
        parser.add_argument('--limite', type=int, default=None, help='Limitar cantidad de profesionales a importar.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limite = options['limite']

        self.stdout.write(self.style.NOTICE("=== Importación de Profesionales de OPD ==="))
        self.stdout.write(f"Modo: {'DRY RUN (Simulación)' if dry_run else 'REAL'}")
        self.stdout.write(f"Contraseña genérica asignada: '{DEFAULT_PASSWORD}'")
        if limite:
            self.stdout.write(f"Límite: {limite}")

        if not os.path.exists(EXCEL_PERSONAL_PATH):
            self.stderr.write(f"Error: No se encontró el archivo {EXCEL_PERSONAL_PATH}")
            return

        # Cargar catálogo de instituciones en BD
        inst_dict = {i.nombre: i for i in Institucion.objects.all()}

        wb = openpyxl.load_workbook(EXCEL_PERSONAL_PATH, read_only=True, data_only=True)
        sheet = wb['Nomina_General_OPD']

        creados = 0
        actualizados = 0
        omitidos = 0
        dudosos_sin_cargar = []
        usernames_usados = set(User.objects.values_list('username', flat=True))

        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            if i == 0 or not row: continue

            opd_raw = str(row[2] or '').strip()
            cuil_raw = str(row[3] or '').strip()
            apellido = str(row[4] or '').strip()
            nombre = str(row[5] or '').strip()
            profesion = str(row[6] or '').strip()
            matricula = str(row[7] or '').strip()
            email_raw = str(row[10] or '').strip()
            telefono = str(row[11] or '').strip()
            condicion = str(row[12] or '').strip()
            obs = str(row[13] or '').strip()

            # Procesar filas normales o itinerantes BIS
            es_bis = 'BIS' in condicion

            # 1. Validar Institución
            inst_nombre_bd = MAPA_OPD_A_BD.get(opd_raw)
            if not inst_nombre_bd or inst_nombre_bd not in inst_dict:
                dudosos_sin_cargar.append({
                    'nombre': f"{nombre} {apellido}",
                    'opd_excel': opd_raw,
                    'motivo': f"Institución desconocida o no homologada ('{opd_raw}')"
                })
                continue

            inst_obj = inst_dict[inst_nombre_bd]

            if es_bis:
                # Buscar el usuario ya creado por nombre y apellido
                u_exist = User.objects.filter(
                    first_name__iexact=nombre.strip(),
                    last_name__iexact=apellido.strip()
                ).first()
                if u_exist:
                    if dry_run:
                        self.stdout.write(
                            f"[DRY-RUN ITINERANCIA] {u_exist.username:<15} | {u_exist.get_full_name():<25} | "
                            f"Agrega Inst: {inst_obj.nombre}"
                        )
                    else:
                        perfil, _ = UsuarioPerfil.objects.get_or_create(usuario=u_exist)
                        perfil.es_profesional = True
                        perfil.instituciones.add(inst_obj)
                        if not perfil.id_institucion:
                            perfil.id_institucion = inst_obj
                            perfil.save(update_fields=['id_institucion'])
                        self.stdout.write(
                            f"[ITINERANCIA VINCULADA] {u_exist.username:<15} | {u_exist.get_full_name():<25} | "
                            f"Inst Adicional: {inst_obj.nombre}"
                        )
                    continue

            # 2. Generar Username único
            base_user = generar_username_base(nombre, apellido)
            username = base_user
            contador = 1
            while username in usernames_usados:
                # Comprobar si ya existe el usuario para esta persona
                u_exist = User.objects.filter(username=username).first()
                if u_exist and u_exist.first_name.upper() == nombre.upper() and u_exist.last_name.upper() == apellido.upper():
                    break
                contador += 1
                username = f"{base_user}{contador}"

            email = email_raw if (email_raw and email_raw != '-' and '@' in email_raw) else ''

            if dry_run:
                self.stdout.write(
                    f"[DRY-RUN] Usuario: {username:<15} | {nombre.upper()} {apellido.upper():<20} | "
                    f"Inst: {inst_obj.nombre:<30} | Prof: {profesion}"
                )
                creados += 1
            else:
                with transaction.atomic():
                    user, was_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': nombre.upper(),
                            'last_name': apellido.upper(),
                            'email': email,
                            'is_active': True
                        }
                    )

                    # Si es nuevo, asignar password genérico
                    if was_created:
                        user.set_password(DEFAULT_PASSWORD)
                        user.save()
                        creados += 1
                    else:
                        # Si ya existía, actualizar nombres y correo
                        user.first_name = nombre.upper()
                        user.last_name = apellido.upper()
                        if email: user.email = email
                        user.save()
                        actualizados += 1

                    usernames_usados.add(username)

                    # 3. Asignar perfil profesional y vincular con sus instituciones
                    perfil, _ = UsuarioPerfil.objects.get_or_create(usuario=user)
                    perfil.es_profesional = True
                    if not perfil.id_institucion:
                        perfil.id_institucion = inst_obj
                    perfil.save(update_fields=['es_profesional', 'id_institucion'])
                    perfil.instituciones.add(inst_obj)

                    self.stdout.write(
                        f"[{'CREADO' if was_created else 'ACTUALIZADO'}] {user.username:<15} | "
                        f"{user.get_full_name():<25} | Institución: {inst_obj.nombre}"
                    )

            if limite and (creados + actualizados) >= limite:
                self.stdout.write(self.style.WARNING(f"Alcanzado el límite de {limite}."))
                break

        wb.close()

        self.stdout.write(self.style.SUCCESS("\n=== Resumen de Importación de Profesionales ==="))
        self.stdout.write(f"Profesionales creados: {creados}")
        self.stdout.write(f"Profesionales actualizados: {actualizados}")
        self.stdout.write(f"Dudosos dejados sin cargar: {len(dudosos_sin_cargar)}")

        if dudosos_sin_cargar:
            self.stdout.write(self.style.WARNING("\nListado de personas con institución dudosa para revisión:"))
            for d in dudosos_sin_cargar:
                self.stdout.write(f"  - {d['nombre']}: {d['motivo']}")
