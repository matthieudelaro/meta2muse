from unittest import TestCase
import pandas as pd

from parameters import column_infos_from_header
from toxml import row_to_field


class Tests(TestCase):
    def test_row_to_field(self):
        xlsx = pd.read_excel('./metadata_tests.xlsx')
        xlsx = xlsx[3:]
        header = pd.read_excel('./metadata_tests.xlsx')

        column_info = column_infos_from_header(header)

        row = xlsx.iloc[0]
        res = row_to_field('titre', (0, row), column_info)
        self.assertEqual(res, 'titre')
        res = row_to_field('cote_secli', (0, row), column_info)
        self.assertEqual(res, None)

        row = xlsx.iloc[5]
        res = row_to_field('titre', (0, row), column_info)
        self.assertEqual(res, 'titre.1')

        row = xlsx.iloc[7]
        res = row_to_field('cote_secli', (0, row), column_info)
        self.assertEqual(res, 'cote_secli')
        pass
