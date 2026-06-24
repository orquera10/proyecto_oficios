from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .forms import OficioForm, OficioJudicialForm


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
