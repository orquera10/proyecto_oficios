import os
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.core import mail
from django.contrib.messages import get_messages
from django.utils import timezone

from core.models import Sector, UsuarioPerfil
from casos.models import Caso
from personas.models import Nino

from .forms import OficioForm, OficioJudicialForm, OficioMPAForm, NotaForm
from .filters import OficioFilter
from .models import Oficio, OficioMPA, OficioJudicial, Nota, Institucion, MovimientoOficio, oficio_upload_path


class AsignacionEmailTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='asignacion_mail')
        self.client.force_login(self.user)
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.overrides = self.settings(MEDIA_ROOT=self.media.name, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
        self.overrides.enable()
        self.addCleanup(self.overrides.disable)
        self.institucion = Institucion.objects.create(nombre='Destino', email='destino@example.com')
        self.oficio = Oficio.objects.create(archivo_pdf=SimpleUploadedFile('oficio.pdf', b'%PDF-1.4 original oficio'))
        self.url = reverse('oficios:enviar', args=[self.oficio.pk])
        self.data = {'nuevo_estado': 'asignado', 'institucion': self.institucion.pk, 'detalle': 'Solicitar informe'}

    def test_assign_without_mail(self):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(callbacks, [])
        self.assertEqual(len(mail.outbox), 0)
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'asignado')

    def test_sends_original_to_selected_institution_with_custom_subject(self):
        original = Institucion.objects.create(nombre='Anterior', email='anterior@example.com')
        self.oficio.institucion = original
        self.oficio.save()
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(self.url, {**self.data, 'enviar_email': 'on', 'asunto_email': 'Pedido de informe'})
            self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(callbacks), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['destino@example.com'])
        self.assertEqual(message.subject, 'Pedido de informe')
        self.assertEqual(message.body, f'Se adjunta una copia del oficio {self.oficio.codigo}.')
        self.assertNotIn('SOLICITAR INFORME', message.message().as_string())
        self.assertEqual(self.oficio.movimientos.get().detalle, 'SOLICITAR INFORME')
        self.assertEqual(message.attachments[0][1], b'%PDF-1.4 original oficio')
        self.assertEqual(message.attachments[0][2], 'application/pdf')

    def test_invalid_subject_recipient_or_missing_file_prevents_assignment(self):
        for subject in ('', 'Asunto\r\nBcc: otro@example.com', 'x' * 201):
            self.client.post(self.url, {**self.data, 'enviar_email': 'on', 'asunto_email': subject})
            self.oficio.refresh_from_db()
            self.assertEqual(self.oficio.estado, 'cargado')
        self.institucion.email = ''
        self.institucion.save()
        self.client.post(self.url, {**self.data, 'enviar_email': 'on', 'asunto_email': 'Oficio'})
        self.assertEqual(self.oficio.movimientos.count(), 0)
        self.institucion.email = 'destino@example.com'
        self.institucion.save()
        self.oficio.archivo_pdf = None
        self.oficio.save()
        self.client.post(self.url, {**self.data, 'enviar_email': 'on', 'asunto_email': 'Oficio'})
        self.assertEqual(self.oficio.movimientos.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_delivery_failure_keeps_assignment(self):
        with patch('oficios.views.EmailMessage.send', side_effect=OSError('SMTP unavailable')):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(self.url, {**self.data, 'enviar_email': 'on', 'asunto_email': 'Oficio'})
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'asignado')
        self.assertEqual(self.oficio.movimientos.count(), 1)
        self.assertTrue(any('no se pudo enviar' in str(msg) for msg in get_messages(response.wsgi_request)))

    def test_manual_email_used_only_when_institution_has_none(self):
        self.institucion.email = ''
        self.institucion.save()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {**self.data, 'enviar_email': 'on',
                'asunto_email': 'Oficio', 'email_institucion': 'manual@example.com'})
        self.assertEqual(mail.outbox[0].to, ['manual@example.com'])
        self.institucion.refresh_from_db()
        self.assertEqual(self.institucion.email, '')

    def test_registered_email_cannot_be_overridden(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {**self.data, 'enviar_email': 'on',
                'asunto_email': 'Oficio', 'email_institucion': 'otro@example.com'})
        self.assertEqual(mail.outbox[0].to, ['destino@example.com'])

    def test_invalid_manual_email_prevents_assignment(self):
        self.institucion.email = ''
        self.institucion.save()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {**self.data, 'enviar_email': 'on',
                'asunto_email': 'Oficio', 'email_institucion': 'correo-invalido'})
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'cargado')
        self.assertEqual(len(mail.outbox), 0)

    def test_custom_message_preserves_lines_and_excludes_internal_detail(self):
        cuerpo = 'Buenos días:\n\nAdjuntamos el oficio para su intervención.\nSaludos.'
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {**self.data, 'enviar_email': 'on',
                'asunto_email': 'Pedido de informe', 'cuerpo_email': cuerpo,
                'detalle': 'OBSERVACIONES INTERNAS DEL COORDINADOR'})
        self.assertEqual(mail.outbox[0].body, cuerpo)
        self.assertNotIn('OBSERVACIONES INTERNAS', mail.outbox[0].body)
        self.assertEqual(self.oficio.movimientos.get().detalle, 'OBSERVACIONES INTERNAS DEL COORDINADOR')

    def test_empty_or_oversized_message_prevents_assignment(self):
        for cuerpo in ('   ', 'x' * 10001):
            with self.captureOnCommitCallbacks(execute=True):
                self.client.post(self.url, {**self.data, 'enviar_email': 'on',
                    'asunto_email': 'Oficio', 'cuerpo_email': cuerpo})
            self.oficio.refresh_from_db()
            self.assertEqual(self.oficio.estado, 'cargado')
        self.assertEqual(len(mail.outbox), 0)

    def test_email_includes_internal_number_with_custom_message(self):
        self.oficio.numero_interno = '007543'
        self.oficio.save()
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(self.url, {**self.data, 'enviar_email': 'on',
                'asunto_email': 'Pedido de informe', 'cuerpo_email': 'Buenos días.\nAdjuntamos el oficio.'})
        self.assertEqual(mail.outbox[0].body, 'Buenos días.\nAdjuntamos el oficio.\n\nNúmero interno: 007543')
        self.assertEqual(mail.outbox[0].subject, 'Pedido de informe')
        self.assertNotIn('SOLICITAR INFORME', mail.outbox[0].body)

    def test_response_has_no_email_option_and_never_sends(self):
        url = reverse('oficios:responder', args=[self.oficio.pk])
        self.assertNotContains(self.client.get(url), 'name="enviar_email"')
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(url, {'fecha_hora': '2026-09-16T10:00', 'respuesta': 'Respuesta',
                'enviar_email': 'on', 'asunto_email': 'No enviar'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(callbacks, [])
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.oficio.respuestas.count(), 1)


class OficioRevisionTests(TestCase):
    def setUp(self):
        self.users = {}
        for nombre in ('Coordinador', 'Director Niñez', 'Coordinacion OPD', 'Informatica', 'Despacho Niñez', 'Profesional'):
            user = get_user_model().objects.create_user(username=nombre)
            sector = Sector.objects.create(nombre=nombre)
            UsuarioPerfil.objects.create(usuario=user, id_sector=sector)
            self.users[nombre] = user
        self.institucion = Institucion.objects.create(nombre='Institucion inicial')
        self.destino = Institucion.objects.create(nombre='Institucion correctora')
        self.oficio = Oficio.objects.create(
            estado='respondido', institucion=self.institucion,
            validado_coord=False, validado_director=False,
        )

    def post(self, role, action, data=None):
        self.client.force_login(self.users[role])
        return self.client.post(reverse('oficios:' + action, args=[self.oficio.pk]), data or {})

    def test_complete_correction_cycle(self):
        self.oficio.validado_coord = True
        self.oficio.save()
        self.post('Director Niñez', 'enviar_revision', {'detalle': 'Corregir el informe'})
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'en_revision')
        self.assertTrue(self.oficio.revision_pendiente)
        self.assertFalse(self.oficio.validado_coord)
        self.assertFalse(self.oficio.validado_director)
        self.assertEqual(self.oficio.movimientos.get().detalle, 'CORREGIR EL INFORME')
        self.post('Coordinacion OPD', 'enviar', {
            'nuevo_estado': 'asignado', 'institucion': self.destino.pk, 'detalle': 'Corregir el informe',
        })
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'asignado')
        self.assertEqual(self.oficio.institucion, self.destino)
        self.post('Coordinacion OPD', 'responder', {
            'respuesta': 'Informe corregido', 'fecha_hora': '2026-09-16T10:00',
        })
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'respondido')
        self.assertFalse(self.oficio.revision_pendiente)
        self.assertFalse(self.oficio.validado_coord)
        self.assertFalse(self.oficio.validado_director)
        self.assertEqual(self.oficio.respuestas.count(), 1)
        self.post('Director Niñez', 'validar_director')
        self.oficio.refresh_from_db()
        self.assertFalse(self.oficio.validado_director)
        self.post('Coordinador', 'validar_coord')
        self.post('Director Niñez', 'validar_director')
        self.oficio.refresh_from_db()
        self.assertTrue(self.oficio.validado_coord)
        self.assertTrue(self.oficio.validado_director)

    def test_revision_requires_reviewer_response_and_reason(self):
        for role in ('Coordinacion OPD', 'Informatica', 'Despacho Niñez', 'Profesional'):
            self.post(role, 'enviar_revision', {'detalle': 'Corregir'})
            self.oficio.refresh_from_db()
            self.assertEqual(self.oficio.estado, 'respondido')
        self.post('Coordinador', 'enviar_revision', {'detalle': '  '})
        self.assertFalse(self.oficio.movimientos.exists())
        self.post('Coordinador', 'enviar_revision', {'detalle': 'Corregir'})
        self.post('Coordinador', 'enviar_revision', {'detalle': 'Repetido'})
        self.assertEqual(self.oficio.movimientos.count(), 1)

    def test_only_opd_can_assign_and_respond_in_correction_cycle(self):
        self.post('Coordinador', 'enviar_revision', {'detalle': 'Corregir'})
        for role in self.users:
            with self.subTest(role=role):
                self.client.force_login(self.users[role])
                detail = self.client.get(reverse('oficios:detail', args=[self.oficio.pk]))
                if role == 'Coordinacion OPD':
                    self.assertContains(detail, 'data-bs-target="#asignarModal"')
                else:
                    self.assertNotContains(detail, 'data-bs-target="#asignarModal"')
                    self.post(role, 'enviar', {'nuevo_estado': 'asignado', 'institucion': self.destino.pk})
                self.post(role, 'responder', {'respuesta': 'No corresponde', 'fecha_hora': '2026-09-16T10:00'})
                self.oficio.refresh_from_db()
                self.assertEqual(self.oficio.estado, 'en_revision')
                self.assertEqual(self.oficio.respuestas.count(), 0)
        self.post('Coordinacion OPD', 'enviar', {'nuevo_estado': 'asignado', 'institucion': self.destino.pk})
        for role in self.users:
            self.client.force_login(self.users[role])
            detail = self.client.get(reverse('oficios:detail', args=[self.oficio.pk]))
            if role == 'Coordinacion OPD':
                self.assertContains(detail, 'id="btnResponder"')
            else:
                self.assertNotContains(detail, 'id="btnResponder"')
                self.post(role, 'responder', {'respuesta': 'No corresponde', 'fecha_hora': '2026-09-16T10:00'})
        self.assertEqual(self.oficio.respuestas.count(), 0)

    def test_generic_movement_cannot_bypass_review(self):
        self.post('Informatica', 'enviar', {'nuevo_estado': 'en_revision'})
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'respondido')
        self.post('Coordinador', 'enviar_revision', {'detalle': 'Corregir'})
        for estado in ('respondido', 'enviado', 'cargado', 'incompetencia'):
            self.post('Coordinacion OPD', 'enviar', {'nuevo_estado': estado})
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.estado, 'en_revision')
        self.assertEqual(self.oficio.movimientos.count(), 1)

    def test_review_button_disappears_after_each_roles_approval(self):
        for role, action in (('Coordinador', 'validar_coord'), ('Director Niñez', 'validar_director')):
            with self.subTest(role=role):
                self.client.force_login(self.users[role])
                url = reverse('oficios:detail', args=[self.oficio.pk])
                self.assertContains(self.client.get(url), 'data-bs-target="#revisionModal"')
                self.post(role, action)
                self.assertNotContains(self.client.get(url), 'data-bs-target="#revisionModal"')
                before = self.oficio.movimientos.count()
                self.post(role, 'enviar_revision', {'detalle': 'No debe permitirse'})
                self.oficio.refresh_from_db()
                self.assertEqual(self.oficio.estado, 'respondido')
                self.assertTrue(self.oficio.validado_coord)
                if role == 'Director Niñez':
                    self.assertTrue(self.oficio.validado_director)
                self.assertEqual(self.oficio.movimientos.count(), before)

    def test_removing_approval_restores_review_action(self):
        self.post('Coordinador', 'validar_coord')
        self.post('Coordinador', 'validar_coord')
        response = self.client.get(reverse('oficios:detail', args=[self.oficio.pk]))
        self.assertContains(response, 'data-bs-target="#revisionModal"')


class OficioMultiInstitucionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='multi_institucion')
        self.client.force_login(self.user)
        self.instituciones = [Institucion.objects.create(nombre=nombre) for nombre in ('Primera', 'Segunda')]
        self.caso = Caso.objects.create(usuario=self.user)

    def test_single_or_no_institution_still_creates_one_document(self):
        for instituciones in ([], [self.instituciones[0].pk]):
            before = Oficio.objects.count()
            response = self.client.post(reverse('oficios:create_tipo', kwargs={'tipo': 'nota'}), {
                'fecha_emision': '2026-09-16T10:00', 'instituciones': instituciones,
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Oficio.objects.count(), before + 1)
            obj = Oficio.objects.latest('pk')
            self.assertEqual(obj.institucion_id, instituciones[0] if instituciones else None)
            self.assertEqual(obj.movimientos.count(), 1)

    def test_attachment_saved_for_both_documents(self):
        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            content = b'%PDF-1.4 test attachment'
            response = self.client.post(reverse('oficios:create_tipo', kwargs={'tipo': 'nota'}), {
                'fecha_emision': '2026-09-16T10:00',
                'instituciones': [inst.pk for inst in self.instituciones],
                'archivo_pdf': SimpleUploadedFile('oficio.pdf', content, content_type='application/pdf'),
            })
            self.assertEqual(response.status_code, 302)
            documentos = list(Oficio.objects.all())
            self.assertEqual(len(documentos), 2)
            self.assertNotEqual(documentos[0].archivo_pdf.name, documentos[1].archivo_pdf.name)
            for obj in documentos:
                with obj.archivo_pdf.open('rb') as uploaded:
                    self.assertEqual(uploaded.read(), content)

    def test_failure_rolls_back_all_documents_and_initial_movements(self):
        create = MovimientoOficio.objects.create
        calls = 0

        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError('Simulated movement failure')
            return create(**kwargs)

        with patch.object(MovimientoOficio.objects, 'create', side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse('oficios:create_tipo', kwargs={'tipo': 'nota'}), {
                    'fecha_emision': '2026-09-16T10:00',
                    'instituciones': [inst.pk for inst in self.instituciones],
                    'caso': self.caso.pk,
                })
        self.assertEqual(Oficio.objects.count(), 0)
        self.assertEqual(MovimientoOficio.objects.count(), 0)
        self.caso.refresh_from_db()
        self.assertEqual(self.caso.estado, 'ABIERTO')

    def test_creates_independent_documents_for_each_institution(self):
        for tipo, model, extra in (
            ('mpa', OficioMPA, {'nro_oficio': '401/25'}),
            ('judicial', OficioJudicial, {'expediente': 'VJ-16791/2026'}),
            ('nota', Nota, {}),
        ):
            with self.subTest(tipo=tipo):
                response = self.client.post(reverse('oficios:create_tipo', kwargs={'tipo': tipo}), {
                    'fecha_emision': '2026-09-16T10:00',
                    'numero_interno': '7543',
                    'caso': self.caso.pk,
                    'instituciones': [inst.pk for inst in self.instituciones],
                    'plazo_horas': 2,
                    'plazo_unidad': 'dias',
                    **extra,
                })
                self.assertEqual(response.status_code, 302)
                documentos = list(model.objects.all().order_by('institucion_id'))
                self.assertEqual(len(documentos), 2)
                self.assertEqual(len({obj.codigo for obj in documentos}), 2)
                for obj, inst in zip(documentos, self.instituciones):
                    self.assertEqual(obj.institucion, inst)
                    self.assertEqual(obj.numero_interno, '7543')
                    self.assertEqual(obj.caso, self.caso)
                    self.assertEqual(obj.plazo_horas, 48)
                    self.assertIsNotNone(obj.fecha_vencimiento)
                    self.assertEqual(obj.movimientos.count(), 1)
                    self.assertEqual(obj.movimientos.get().institucion, inst)
                documentos[0].estado = 'asignado'
                documentos[0].save()
                documentos[1].refresh_from_db()
                self.assertEqual(documentos[1].estado, 'cargado')
        self.caso.refresh_from_db()
        self.assertEqual(self.caso.estado, 'EN_PROCESO')


class DniNinoFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='dni_filter')
        caso = Caso.objects.create(usuario=self.user)
        caso.ninos.add(
            Nino.objects.create(nombre='Ana', apellido='Prueba', dni='51.108.431'),
            Nino.objects.create(nombre='Luis', apellido='Prueba', dni='52123456'),
        )
        self.oficio = Oficio.objects.create(caso=caso)
        self.otro = Oficio.objects.create()

    def test_matches_formatted_and_unformatted_dni(self):
        for dni in ('51108431', '51.108.431', '51 108 431', '52.123.456'):
            with self.subTest(dni=dni):
                self.assertEqual(list(OficioFilter({'dni_nino': dni}).qs), [self.oficio])

    def test_empty_unknown_and_combined_filters(self):
        self.assertEqual(OficioFilter({'dni_nino': ''}).qs.count(), 2)
        for dni in ('51108', '99999999', '...'):
            self.assertFalse(OficioFilter({'dni_nino': dni}).qs.exists())
        self.assertFalse(OficioFilter({'dni_nino': '51108431', 'estado': 'enviado'}).qs.exists())

    def test_list_displays_filter_and_matching_oficio(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('oficios:list'), {'dni_nino': '51108431'})
        self.assertContains(response, 'name="dni_nino"')
        self.assertContains(response, self.oficio.codigo)
        self.assertNotContains(response, self.otro.codigo)


class NumeroInternoTests(TestCase):
    def test_search_by_code_or_internal_number(self):
        oficio = Oficio.objects.create(numero_interno='7543', nro_oficio='775068')
        Oficio.objects.create(numero_interno='7544')
        for query in (oficio.codigo, oficio.codigo.lower(), '7543', '775068'):
            with self.subTest(query=query):
                self.assertEqual(list(OficioFilter({'busqueda': query}).qs), [oficio])

    def test_create_and_edit_preserve_identifier_and_history(self):
        form = OficioForm(data={
            'numero_interno': '0012/2026',
            'fecha_emision': '2026-09-16T10:00',
        })
        self.assertTrue(form.is_valid(), form.errors)
        oficio = form.save()
        codigo = oficio.codigo
        oficio.refresh_from_db()
        self.assertEqual(oficio.numero_interno, '0012/2026')
        form = OficioForm(instance=oficio, data={
            'numero_interno': '0013/2026',
            'fecha_emision': '2026-09-16T10:00',
        })
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        oficio.refresh_from_db()
        self.assertEqual(oficio.numero_interno, '0013/2026')
        self.assertEqual(oficio.codigo, codigo)
        self.assertEqual(oficio.history.first().numero_interno, '0013/2026')

    def test_optional_in_all_document_forms(self):
        for form_class in (OficioForm, OficioJudicialForm, OficioMPAForm, NotaForm):
            with self.subTest(form=form_class.__name__):
                self.assertFalse(form_class().fields['numero_interno'].required)
        self.assertEqual(Oficio.objects.create().numero_interno, '')

    def test_search_and_display(self):
        oficio = Oficio.objects.create(numero_interno='00987/2026')
        Oficio.objects.create()
        results = OficioFilter({'busqueda': '00987'}).qs
        self.assertEqual(list(results), [oficio])
        user = get_user_model().objects.create_user(username='internos')
        self.client.force_login(user)
        for url in (reverse('oficios:list'), reverse('oficios:detail', args=[oficio.pk])):
            with self.subTest(url=url):
                self.assertContains(self.client.get(url), '00987/2026')
        self.assertContains(
            self.client.get(reverse('oficios:update', args=[oficio.pk])),
            'name="numero_interno"',
        )


class OficioUploadPathTests(SimpleTestCase):
    def test_long_filename_is_shortened_without_losing_extension(self):
        instance = SimpleNamespace(fecha_emision=timezone.now())
        filename = (
            '7708_CORONEL_ARIAS.1.3884099342_SOTO_IRMA_DIRECTORA_'
            'DOCUMENTACION_ADJUNTA_CON_NOMBRE_MUY_EXTENSO.pdf'
        )

        path = oficio_upload_path(instance, filename)

        self.assertLessEqual(len(path), 100)
        self.assertEqual(os.path.splitext(path)[1], '.pdf')
        self.assertNotIn('.', os.path.splitext(os.path.basename(path))[0])


class OficioFormUploadTests(TestCase):
    def test_accepts_zip_and_rar_files(self):
        form = OficioForm()
        self.assertIn('.zip', form.fields['archivo_pdf'].widget.attrs['accept'])
        self.assertIn('.rar', form.fields['archivo_pdf'].widget.attrs['accept'])

        uploaded = SimpleUploadedFile(
            'archivo.zip',
            b'zip-data',
            content_type='application/zip',
        )
        form = OficioForm(files={'archivo_pdf': uploaded})
        self.assertTrue(form.is_valid())


class OficioJudicialFormTests(TestCase):
    def test_accepts_any_leading_letter_in_expediente(self):
        form = OficioJudicialForm(data={
            'fecha_emision': '2025-01-01T10:00',
            'expediente': 'A-244216/2024',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['expediente'], 'A-244216/2024')

    def test_accepts_multi_letter_prefix_in_expediente(self):
        form = OficioJudicialForm(data={
            'fecha_emision': '2026-01-01T10:00',
            'expediente': 'VJ-16791/2026',
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['expediente'], 'VJ-16791/2026')


class OficioDespachoPermissionsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username='despacho',
            password='test-password',
        )
        sector = Sector.objects.create(nombre='Despacho Niñez')
        UsuarioPerfil.objects.create(usuario=self.user, id_sector=sector)
        self.oficio = Oficio.objects.create(
            nro_oficio='100/2026',
            usuario=self.user,
        )
        self.client.force_login(self.user)

    def test_despacho_can_update_an_oficio(self):
        response = self.client.post(
            reverse('oficios:update', kwargs={'pk': self.oficio.pk}),
            {
                'nro_oficio': '101/2026',
                'fecha_emision': timezone.localtime(
                    self.oficio.fecha_emision
                ).strftime('%Y-%m-%dT%H:%M'),
                'plazo_unidad': 'horas',
            },
        )

        self.assertRedirects(
            response,
            reverse('oficios:detail', kwargs={'pk': self.oficio.pk}),
        )
        self.oficio.refresh_from_db()
        self.assertEqual(self.oficio.nro_oficio, '101/2026')

    def test_despacho_still_cannot_respond_to_an_oficio(self):
        response = self.client.get(
            reverse('oficios:responder', kwargs={'pk': self.oficio.pk})
        )

        self.assertRedirects(
            response,
            reverse('oficios:detail', kwargs={'pk': self.oficio.pk}),
        )

    def test_list_renders_when_both_caratula_fields_are_empty(self):
        self.assertIsNone(self.oficio.caratula_oficio)
        self.assertIsNone(self.oficio.caratula)

        response = self.client.get(reverse('oficios:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Car&aacute;tula del documento:')
