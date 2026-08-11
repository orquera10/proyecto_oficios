import os
from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Sector, UsuarioPerfil

from .forms import OficioForm, OficioJudicialForm
from .models import Oficio, oficio_upload_path


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
