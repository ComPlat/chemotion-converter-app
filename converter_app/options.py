DATA_TYPES = (
    'INFRARED SPECTRUM',
    'RAMAN SPECTRUM',
    'INFRARED PEAK TABLE',
    'INFRARED INTERFEROGRAM',
    'INFRARED TRANSFERED SPECTRUM',
    'NMR FID',
    'NMR SPECTRUM',
    'NMR PEAK TABLE',
    'NMP PEAK ASSIGNMENTS',
    'MASS SPECTRUM',
    'CONTINUOUS MASS SPECTRUM',
    'THERMOGRAVIMETRIC ANALYSIS',
    'UV-VIS',
    'HPLC UV-VIS',
    'GEL PERMEATION CHROMATOGRAPHY',
    'CYCLIC VOLTAMMETRY',
    'X-RAY DIFFRACTION',
    'AIF' # Must be extened
)

DATA_CLASSES = (
    'XYPOINTS',
    'XYDATA',
    'PEAK TABLE',
    'NTUPLES',
)

XUNITS = (
    'p/p0', # Normalaized dimension
    'kPa',
    '1/CM',
    '2Theta',
    'DEGREES CELSIUS',
    'HZ',
    'MICROMETERS',
    'MINUTES',
    'm/z',
    'NANOMETERS',
    'SECONDS',
    'Voltage vs Ref'
)

YUNITS = (
    'ml/g',
    'mmol/g',
    'ABSORBANCE',
    'Ampere',
    'ARBITRARY UNITS',
    'COUNTS',
    'DERIVATIVE WEIGHT',
    'Intensity',
    'KUBELKA-MUNK',
    'mAU',
    'REFLECTANCE',
    'TRANSMITTANCE',
    'WEIGHT',
)

OPTIONS = {
    'DATA TYPE': DATA_TYPES,
    'DATA CLASS': DATA_CLASSES,
    'XUNITS': XUNITS,
    'YUNITS': YUNITS,
}
