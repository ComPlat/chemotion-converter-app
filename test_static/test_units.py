import astropy.units as u
from converter_app.utils import normalize_unit
from converter_app.datasets import Dataset
u.imperial.enable()

def test_units():
    for x in Dataset.dataset_units():
        for unit in x['units']:
            unit_str = normalize_unit(unit['label'])
            unit = u.Unit(unit_str)
            pass
