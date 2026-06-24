from pathlib import Path

from django.test import SimpleTestCase


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
