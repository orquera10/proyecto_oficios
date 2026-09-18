import os
import re
import shutil
import uuid
import datetime
import unicodedata
import openpyxl
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from oficios.models import Oficio, Juzgado, Institucion, Caratula, MovimientoOficio
from casos.models import Caso, CasoNino, CasoParte
from personas.models import Nino, Parte

User = get_user_model()

EXCEL_PATH = r'\\snfserver2\DESPACHOniñez\OficiosJudiciales2.xlsx'
PDFS_BASE_PATH = r'\\snfserver2\EscaneosBkp\DESPACHO INGRESOS JUDICIALES\OFICIOS 2026'

def clean_dni(val):
    if not val:
        return []
    val_str = str(val).strip()
    raw_nums = re.findall(r'\b\d{1,2}(?:\.\d{3}){2}\b|\b\d{7,8}\b', val_str)
    cleaned = []
    for n in raw_nums:
        d = n.replace('.', '').strip()
        if len(d) in (7, 8) and d.isdigit() and d not in cleaned:
            cleaned.append(d)
    return cleaned

def parse_personas(partes_str):
    if not partes_str:
        return [], []

    text = str(partes_str).replace('\n', ' ').strip()
    partes_adultas_raw = []
    ninos_raw = []

    c_match = re.split(r'\s+(?:C\/|CONTRA)\s+', text, flags=re.IGNORECASE)
    if len(c_match) > 1:
        partes_adultas_raw.append(c_match[0].strip())
        resto = c_match[1].strip()
        tokens = re.split(r'\s+-\s+|\s+Y\s+', resto)
        ninos_raw.extend([t.strip() for t in tokens if t.strip()])
    else:
        tokens = re.split(r'\s+-\s+|\s+Y\s+', text)
        ninos_raw.extend([t.strip() for t in tokens if t.strip()])

    ninos_clean = [n for n in ninos_raw if len(n) > 2 and not n.isdigit()]
    partes_clean = [p for p in partes_adultas_raw if len(p) > 2 and not p.isdigit()]

    return ninos_clean, partes_clean

def split_nombre_apellido(nombre_completo):
    parts = nombre_completo.strip().split()
    if len(parts) == 1:
        return parts[0].upper(), 'S/A'
    elif len(parts) == 2:
        return parts[0].upper(), parts[1].upper()
    elif len(parts) == 3:
        return f"{parts[0]} {parts[1]}".upper(), parts[2].upper()
    else:
        mid = len(parts) // 2
        return " ".join(parts[:mid]).upper(), " ".join(parts[mid:]).upper()

def normalizar_texto(t):
    if not t:
        return ''
    t = unicodedata.normalize('NFKD', str(t)).encode('ASCII', 'ignore').decode('utf-8')
    t = re.sub(r'[^A-Z0-9\s]', ' ', t.upper())
    return ' '.join(t.split())

def match_institucion_cargada(raw_name, instituciones_list):
    if not raw_name:
        return None

    raw_norm = normalizar_texto(raw_name)
    if not raw_norm:
        return None

    if '102' in raw_norm:
        for inst in instituciones_list:
            if 'LINEA 102' in normalizar_texto(inst.nombre):
                return inst

    if 'DISPOSITIVO' in raw_norm:
        for inst in instituciones_list:
            if 'DISPOSITIVO' in normalizar_texto(inst.nombre):
                return inst

    if 'LGSM' in raw_norm or 'LIBERTADOR' in raw_norm:
        for inst in instituciones_list:
            if 'LIBERTADOR' in normalizar_texto(inst.nombre):
                return inst

    if 'ALTO' in raw_norm:
        if '1' in raw_norm or 'UNO' in raw_norm:
            for inst in instituciones_list:
                if 'ALTO COMEDERO 1' in normalizar_texto(inst.nombre):
                    return inst
        elif '2' in raw_norm or 'DOS' in raw_norm:
            for inst in instituciones_list:
                if 'ALTO COMEDERO 2' in normalizar_texto(inst.nombre):
                    return inst
        elif '3' in raw_norm or 'TRES' in raw_norm:
            for inst in instituciones_list:
                if 'ALTO COMEDERO 3' in normalizar_texto(inst.nombre):
                    return inst

    if 'SEDE' in raw_norm and 'MAYOR' not in raw_norm:
        for inst in instituciones_list:
            if inst.nombre == 'SEDE':
                return inst

    cleaned_input = raw_norm.replace('O P D N N A', '').replace('OPDNNA', '').replace('OPD', '').strip()
    words_input = [w for w in cleaned_input.split() if len(w) > 2]

    for inst in instituciones_list:
        inst_norm = normalizar_texto(inst.nombre)
        inst_key = inst_norm.replace('O P D N N A', '').replace('OPDNNA', '').replace('OPD', '').strip()
        if cleaned_input and (cleaned_input == inst_key or cleaned_input == inst_norm):
            return inst

    for word in words_input:
        for inst in instituciones_list:
            inst_norm = normalizar_texto(inst.nombre)
            inst_key = inst_norm.replace('O P D N N A', '').replace('OPDNNA', '').replace('OPD', '').strip()
            if word in inst_key.split():
                return inst

    for inst in instituciones_list:
        inst_norm = normalizar_texto(inst.nombre)
        if cleaned_input and (cleaned_input in inst_norm or inst_norm in cleaned_input):
            return inst

    for inst in instituciones_list:
        if inst.nombre == 'SIN ESPECIFICAR':
            return inst

    return None

def match_juzgado_cargado(raw_name, juzgados_list):
    """
    Busca coincidencia contra los 769 Juzgados/Agentes ya cargados en el sistema.
    Evita crear duplicados para MPA, Violencia de Género, Juzgados de Menores, etc.
    """
    if not raw_name:
        return None

    raw_norm = normalizar_texto(raw_name)
    if not raw_norm:
        return None

    # 1. Coincidencia exacta normalizada
    for j in juzgados_list:
        if raw_norm == normalizar_texto(j.nombre):
            return j

    # 2. Tratamiento especial MPA / Fiscalía
    if any(k in raw_norm for k in ['MPA', 'M P A', 'ACUSACION', 'MINISTERIO PUBLICO']):
        # Intentar coincidir delegaciones específicas de MPA si existen
        sub_tokens = [w for w in raw_norm.split() if w not in ['MPA', 'M', 'P', 'A', 'MINISTERIO', 'PUBLICO', 'DE', 'LA', 'ACUSACION', 'FISCALIA', 'ESPECIALIZADA']]
        best_mpa = None
        best_score = 0
        for j in juzgados_list:
            j_norm = normalizar_texto(j.nombre)
            if 'MPA' in j_norm or 'M P A' in j_norm or 'FISCAL' in j_norm:
                score = sum(1 for st in sub_tokens if st in j_norm)
                if score > best_score:
                    best_score = score
                    best_mpa = j
        if best_mpa:
            return best_mpa

        # Si no hay delegación específica, asignar la entidad MPA general existente
        for j in juzgados_list:
            if j.nombre in ['M.P.A', 'MP A', 'MINISTERIO PUBLICO DE LA ACUSACION']:
                return j

    # 3. Coincidencia difusa para Juzgados y Hospitales (palabras clave esenciales)
    stop_words = {'JUZGADO', 'DE', 'DEL', 'LA', 'LOS', 'LAS', 'PRIMERA', 'INSTANCIA', 'SEGUNDA', 'NUMERO', 'N'}
    r_words = [w for w in raw_norm.split() if len(w) > 2 and w not in stop_words]

    best_match = None
    best_score = 0
    for j in juzgados_list:
        j_norm = normalizar_texto(j.nombre)
        score = sum(1 for w in r_words if w in j_norm)
        if score > best_score and score >= max(1, len(r_words) * 0.6):
            best_score = score
            best_match = j

    if best_match:
        return best_match

    # 4. Si no coincide, buscar 'SIN ESPECIFICAR'
    for j in juzgados_list:
        if j.nombre == 'SIN ESPECIFICAR':
            return j

    return None


class Command(BaseCommand):
    help = 'Migra oficios del año 2026 vinculando a Niños, Casos, y usando solo instituciones y juzgados existentes.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Simular sin guardar en base de datos ni copiar archivos.')
        parser.add_argument('--limite', type=int, default=None, help='Limitar la cantidad de registros a procesar.')
        parser.add_argument('--con-archivos', action='store_true', help='Copiar PDFs a media local y asociarlos al oficio.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limite = options['limite']
        con_archivos = options['con_archivos']

        self.stdout.write(self.style.NOTICE("=== Iniciando Migración Integral de Oficios 2026 ==="))
        self.stdout.write(f"Modo: {'DRY RUN (Simulación)' if dry_run else 'REAL'}")
        self.stdout.write(f"Copia de PDFs: {'Activada' if con_archivos else 'Desactivada'}")
        if limite:
            self.stdout.write(f"Límite: {limite} registros")

        usuario_default, _ = User.objects.get_or_create(
            username='migracion_sistema',
            defaults={
                'first_name': 'Sistema',
                'last_name': 'Migración',
                'email': 'migracion@snaf.mdsjujuy.gov.ar',
                'is_active': True
            }
        )

        # Cargar catálogos preexistentes
        instituciones_existentes = list(Institucion.objects.all())
        juzgados_existentes = list(Juzgado.objects.all())
        self.stdout.write(self.style.SUCCESS(f"Instituciones cargadas: {len(instituciones_existentes)} | Juzgados/Agentes cargados: {len(juzgados_existentes)}"))

        # Indexar PDFs
        pdf_index = {}
        if con_archivos or dry_run:
            self.stdout.write(self.style.NOTICE("Indexando archivos PDF en 'OFICIOS 2026'..."))
            if os.path.exists(PDFS_BASE_PATH):
                for root, _, files in os.walk(PDFS_BASE_PATH):
                    for f in files:
                        if f.lower().endswith('.pdf'):
                            match = re.match(r'^(\d+)', f.strip())
                            if match:
                                num = int(match.group(1))
                                if num not in pdf_index:
                                    pdf_index[num] = os.path.join(root, f)
                self.stdout.write(self.style.SUCCESS(f"Total PDFs indexados: {len(pdf_index)}"))
            else:
                self.stderr.write(f"Advertencia: No se pudo acceder a la ruta de PDFs: {PDFS_BASE_PATH}")

        # Cargar Excel
        self.stdout.write(self.style.NOTICE(f"Leyendo Excel desde: {EXCEL_PATH}"))
        try:
            wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
            sheet = wb['OficiosJudiciales']
        except Exception as e:
            self.stderr.write(f"Error al abrir Excel: {e}")
            return

        procesados = 0
        creados = 0
        omitidos = 0
        casos_nuevos = 0
        casos_existentes_reusados = 0
        con_pdf_count = 0
        sin_pdf_count = 0

        for row in sheet.iter_rows(values_only=True):
            if not row or row[0] == 'id':
                continue

            f_rec = row[8] if len(row) > 8 else None
            if not (hasattr(f_rec, 'year') and f_rec.year == 2026):
                continue

            interno_val = row[2] if len(row) > 2 else None
            if interno_val is None or str(interno_val).strip() == '':
                continue

            num_interno_str = str(interno_val).strip()

            if Oficio.objects.filter(numero_interno=num_interno_str).exists():
                omitidos += 1
                continue

            procesados += 1

            # Tipo
            tipo_raw = str(row[7] or '').strip().upper()
            if 'JUDICIAL' in tipo_raw:
                tipo_doc = Oficio.TIPO_DOCUMENTO_JUDICIAL
            elif 'MPA' in tipo_raw:
                tipo_doc = Oficio.TIPO_DOCUMENTO_MPA
            elif any(k in tipo_raw for k in ['NOTA', 'EMAIL', 'MAIL', 'ACTA']):
                tipo_doc = Oficio.TIPO_DOCUMENTO_NOTA
            else:
                tipo_doc = Oficio.TIPO_DOCUMENTO_LEGACY

            nro_oficio_val = str(row[9] or '').strip()
            nro_oficio = '' if nro_oficio_val in ['None', '', 'S/N'] else nro_oficio_val[:50]

            # Expediente
            exp_letra = str(row[10] or '').strip() if len(row) > 10 and row[10] else ''
            exp_num = str(row[11] or '').strip() if len(row) > 11 and row[11] else ''
            exp_anio = str(row[12] or '').strip() if len(row) > 12 and row[12] else ''

            exp_partes = []
            if exp_letra: exp_partes.append(exp_letra)
            if exp_num: exp_partes.append(exp_num)
            expediente_str = '-'.join(exp_partes)
            if exp_anio:
                expediente_str = f"{expediente_str}/{exp_anio}" if expediente_str else exp_anio

            # Carátula y Partes
            caratula_raw = str(row[13] or '').strip() if len(row) > 13 and row[13] else ''
            partes_raw = str(row[6] or '').strip() if len(row) > 6 and row[6] else ''

            caratula_oficio_text = ""
            if caratula_raw and partes_raw:
                caratula_oficio_text = f"{caratula_raw} - {partes_raw}"
            elif caratula_raw:
                caratula_oficio_text = caratula_raw
            elif partes_raw:
                caratula_oficio_text = partes_raw
            caratula_oficio_text = caratula_oficio_text[:255].upper()

            # JUZGADO: MATCHING CONTRA LOS 769 CARGADOS
            agente_raw = str(row[14] or '').strip().upper() if len(row) > 14 and row[14] else ''
            juzgado_obj = match_juzgado_cargado(agente_raw, juzgados_existentes)

            # INSTITUCIÓN: MATCHING CONTRA LAS 53 CARGADAS
            inst_raw = str(row[15] or '').strip() if len(row) > 15 and row[15] else ''
            inst_obj = match_institucion_cargada(inst_raw, instituciones_existentes)

            # Fechas y Plazo
            fecha_emision = f_rec
            if isinstance(fecha_emision, datetime.datetime):
                if timezone.is_naive(fecha_emision):
                    fecha_emision = timezone.make_aware(fecha_emision, timezone.get_current_timezone())
            elif isinstance(fecha_emision, datetime.date):
                fecha_emision = timezone.make_aware(
                    datetime.datetime.combine(fecha_emision, datetime.time(9, 0)),
                    timezone.get_current_timezone()
                )
            else:
                fecha_emision = timezone.now()

            plazo_val = None
            if len(row) > 3 and row[3]:
                try:
                    p_match = re.search(r'\d+', str(row[3]))
                    if p_match: plazo_val = int(p_match.group(0))
                except:
                    pass

            # PDF Match
            pdf_path = None
            try:
                num_int_key = int(float(num_interno_str))
                pdf_path = pdf_index.get(num_int_key)
            except ValueError:
                pass

            if pdf_path:
                con_pdf_count += 1
            else:
                sin_pdf_count += 1

            # Parseo Niños y Partes
            dnis = clean_dni(row[4] if len(row) > 4 else None)
            ninos_nombres, partes_adultas_nombres = parse_personas(partes_raw)

            if dry_run:
                if procesados <= 10 or procesados % 500 == 0:
                    self.stdout.write(
                        f"[DRY-RUN] #{procesados} INT: {num_interno_str} | "
                        f"Juzgado: '{agente_raw[:25]}' -> '{juzgado_obj.nombre[:25] if juzgado_obj else 'None'}' | "
                        f"Inst: '{inst_obj.nombre if inst_obj else 'None'}' | PDF: {'SI' if pdf_path else 'NO'}"
                    )
            else:
                with transaction.atomic():
                    # 1. Niños
                    ninos_objs = []
                    for idx, n_nom in enumerate(ninos_nombres):
                        nom, ape = split_nombre_apellido(n_nom)
                        dni_asignar = dnis[idx] if idx < len(dnis) else None
                        nino_obj = None

                        if dni_asignar:
                            nino_obj = Nino.objects.filter(dni=dni_asignar).first()
                        if not nino_obj:
                            nino_obj = Nino.objects.filter(nombre=nom, apellido=ape).first()

                        if not nino_obj:
                            nino_obj = Nino.objects.create(
                                nombre=nom,
                                apellido=ape,
                                dni=dni_asignar
                            )
                        elif dni_asignar and not nino_obj.dni:
                            nino_obj.dni = dni_asignar
                            nino_obj.save(update_fields=['dni'])

                        ninos_objs.append(nino_obj)

                    # 2. Partes
                    partes_objs = []
                    for p_nom in partes_adultas_nombres:
                        p_n, p_a = split_nombre_apellido(p_nom)
                        parte_obj = Parte.objects.filter(nombre=p_n, apellido=p_a).first()
                        if not parte_obj:
                            parte_obj = Parte.objects.create(nombre=p_n, apellido=p_a)
                        partes_objs.append(parte_obj)

                    # 3. Caso
                    caso_existente = None
                    for no in ninos_objs:
                        c_rel = no.casos.order_by('-creado').first()
                        if c_rel:
                            caso_existente = c_rel
                            break

                    if caso_existente:
                        caso_obj = caso_existente
                        casos_existentes_reusados += 1
                    else:
                        caso_obj = Caso(usuario=usuario_default, estado='EN_PROCESO')
                        caso_obj.save()
                        casos_nuevos += 1

                    for no in ninos_objs:
                        CasoNino.objects.get_or_create(caso=caso_obj, nino=no)

                    for po in partes_objs:
                        CasoParte.objects.get_or_create(
                            caso=caso_obj,
                            parte=po,
                            defaults={'tipo_relacion': 'OTRO'}
                        )

                    # 4. Oficio
                    oficio = Oficio(
                        numero_interno=num_interno_str,
                        tipo_documento=tipo_doc,
                        nro_oficio=nro_oficio,
                        expediente=expediente_str[:50] if expediente_str else None,
                        caratula_oficio=caratula_oficio_text or None,
                        juzgado=juzgado_obj,
                        institucion=inst_obj,
                        usuario=usuario_default,
                        fecha_emision=fecha_emision,
                        plazo_horas=plazo_val,
                        caso=caso_obj,
                        estado='cargado'
                    )
                    oficio.save()

                    # 5. Movimiento
                    obs_extra = str(row[16] or '').strip() if len(row) > 16 and row[16] else ''
                    prog_extra = str(row[18] or '').strip() if len(row) > 18 and row[18] else ''
                    inst_nombre_str = inst_obj.nombre if inst_obj else 'SIN ASIGNAR'
                    juzg_nombre_str = juzgado_obj.nombre if juzgado_obj else 'SIN AGENTE'
                    detalle_mov = f"MIGRACIÓN 2026: OFICIO PROCEDENCIA {juzg_nombre_str}, ASIGNADO A {inst_nombre_str} (CASO {caso_obj.codigo})."
                    if obs_extra:
                        detalle_mov += f" OBS: {obs_extra}"
                    if prog_extra:
                        detalle_mov += f" REMISION: {prog_extra}"

                    MovimientoOficio.objects.create(
                        oficio=oficio,
                        usuario=usuario_default,
                        estado_anterior=None,
                        estado_nuevo='cargado',
                        institucion=inst_obj,
                        detalle=detalle_mov[:500]
                    )

                    # 6. Copiar y adjuntar PDF si aplica
                    if con_archivos and pdf_path and os.path.exists(pdf_path):
                        try:
                            filename = os.path.basename(pdf_path)
                            with open(pdf_path, 'rb') as f:
                                oficio.archivo_pdf.save(filename, File(f), save=True)
                        except Exception as err:
                            self.stderr.write(f"Error adjuntando PDF para interno {num_interno_str}: {err}")

                    creados += 1
                    if creados <= 10 or creados % 500 == 0:
                        self.stdout.write(
                            f"[CREADO] #{creados} Oficio: {oficio.codigo} (Int: {num_interno_str}) | "
                            f"Juzgado: {juzgado_obj.nombre[:30] if juzgado_obj else 'None'} | "
                            f"Inst: {inst_obj.nombre if inst_obj else 'None'} | PDF: {'SI' if (con_archivos and pdf_path) else 'NO'}"
                        )

            if limite and procesados >= limite:
                self.stdout.write(self.style.WARNING(f"Alcanzado el límite de {limite} registros."))
                break

        wb.close()

        self.stdout.write(self.style.SUCCESS("\n=== Resumen de Migración ==="))
        self.stdout.write(f"Filas procesadas: {procesados}")
        self.stdout.write(f"Oficios creados: {creados}")
        self.stdout.write(f"Casos nuevos creados: {casos_nuevos}")
        self.stdout.write(f"Casos existentes reutilizados: {casos_existentes_reusados}")
        self.stdout.write(f"Omitidos (ya existentes): {omitidos}")
        self.stdout.write(f"Con PDF vinculado: {con_pdf_count}")
        self.stdout.write(f"Sin PDF vinculado: {sin_pdf_count}")
