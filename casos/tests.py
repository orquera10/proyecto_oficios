from pathlib import Path

from django.test import SimpleTestCase, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from personas.models import Nino
from .models import Caso
from .filters import CasoFilter


class CasoFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='filtros_casos')
        self.caso = Caso.objects.create(usuario=self.user)
        self.caso.ninos.add(
            Nino.objects.create(nombre='Ana', apellido='Prueba', dni='51.108.431'),
            Nino.objects.create(nombre='Luis', apellido='Prueba', dni='52123456'),
        )
        self.otro = Caso.objects.create(usuario=self.user)

    def test_search_by_case_identifier(self):
        for value in (self.caso.codigo, self.caso.codigo.lower()):
            with self.subTest(value=value):
                self.assertEqual(list(CasoFilter({'busqueda': value}).qs), [self.caso])

    def test_filter_by_dni_with_or_without_separators(self):
        for value in ('51108431', '51.108.431', '51 108 431', '52.123.456'):
            with self.subTest(value=value):
                self.assertEqual(list(CasoFilter({'dni_nino': value}).qs), [self.caso])

    def test_empty_unknown_and_combined_filters(self):
        self.assertEqual(CasoFilter({'dni_nino': ''}).qs.count(), 2)
        for value in ('51108', '99999999', '...'):
            self.assertFalse(CasoFilter({'dni_nino': value}).qs.exists())
        self.assertFalse(CasoFilter({'dni_nino': '51108431', 'estado': 'CERRADO'}).qs.exists())

    def test_filtered_list(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('casos:list'), {'dni_nino': '51108431'})
        self.assertContains(response, 'name="dni_nino"')
        self.assertContains(response, '<legend>Niño/a relacionado</legend>', html=True)
        self.assertContains(response, self.caso.codigo)
        self.assertNotContains(response, self.otro.codigo)

    def test_related_office_filters_match_same_document_without_duplicate_cases(self):
        from oficios.models import Oficio

        oficio = Oficio.objects.create(caso=self.caso, codigo='OF-00010-2026', numero_interno='007543')
        Oficio.objects.create(caso=self.caso, numero_interno='007543')
        Oficio.objects.create(caso=self.otro, numero_interno='9999')
        Oficio.objects.create(caso=self.otro, numero_interno='007543')
        Oficio.objects.create(numero_interno='007543')
        self.assertEqual(set(CasoFilter({'numero_interno': '7543'}).qs), {self.caso, self.otro})
        for codigo in (oficio.codigo, oficio.codigo.lower(), '00010'):
            self.assertEqual(list(CasoFilter({'codigo_oficio': codigo}).qs), [self.caso])
        data = {'codigo_oficio': oficio.codigo, 'numero_interno': '007543'}
        self.assertEqual(list(CasoFilter(data).qs), [self.caso])
        Oficio.objects.create(caso=self.caso, numero_interno='9999')
        self.assertFalse(CasoFilter({**data, 'numero_interno': '9999'}).qs.exists())
        self.assertFalse(CasoFilter({**data, 'estado': 'CERRADO'}).qs.exists())
        self.assertFalse(CasoFilter({'codigo_oficio': 'no-existe'}).qs.exists())
        self.client.force_login(self.user)
        response = self.client.get(reverse('casos:list'), data)
        self.assertContains(response, 'name="codigo_oficio"')
        self.assertContains(response, 'name="numero_interno"')
        self.assertContains(response, self.caso.codigo)
        self.assertNotContains(response, self.otro.codigo)



class CasoFormTemplateTests(SimpleTestCase):
    def test_create_case_template_uses_observaciones_for_referente_resguardo(self):
        template_path = Path(__file__).resolve().parent / 'templates' / 'casos' / 'caso_form.html'
        content = template_path.read_text(encoding='utf-8')

        self.assertIn('name="partes-${index}-observaciones"', content)
        self.assertIn("value=\"${parte.observaciones || ''}\"", content)

    def test_case_detail_template_shows_relation_and_observaciones_separately(self):
        template_path = Path(__file__).resolve().parent / 'templates' / 'casos' / 'caso_detail.html'
        content = template_path.read_text(encoding='utf-8')

        self.assertIn('{{ relacion.tipo_relacion|default:"-" }}', content)
        self.assertIn('{{ relacion.observaciones|default:"-" }}', content)
