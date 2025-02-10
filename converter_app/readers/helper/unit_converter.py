import re
from datetime import datetime

# Matrix of terms to search for with Unicode escape sequences
search_terms_matrix = [
    ["KNMF Proposal ID", "Nicht verfügbar", "Nich verfügbar", ""],
    ["Data set name", "kein Eintrag", "Capture File Name Format", "DataSetName"],
    ["File created on", "Datei erstellt am", "Date", "TimeStamp"],
    ["Operator", "Autor", "Nicht verfügbar", "Operator ID"],
    ["Device manufacturer", "Gerätehersteller", "Nicht verfügbar", "DEVICE MANUFACTURER"],
    ["Device model", "Gerätemodell", "Data type", ""],
    ["Serial number", "Seriennummer", "Nicht verfügbar", "Serial NR"],
    ["Measurement device type", "Messgerättyp", "Nicht verfügbar", "MEASUREMENT PRINCIPLE"],
    ["Measurement method", "Messverfahren", "Measurement", "MeasMode"],
    ["Software version", "Softwareversion", "Nicht verfügbar", "Nicht verfügbar"],
    ["Output Data format as set", "Set:.fits/html", "Set:.spm", "Set:.xml"],
    ["Length X", "Länge X", "Scan Size", "Berechnung: ImageWidth*PixelSize"],
    ["Point distance X", "Punktabstand X", "Samps/line", "PixelSize"],
    ["Length Y", "Länge Y", "Aspect Ratio", "Berechnung: ImageHeight*PixelSize"],
    ["Point distance Y", "Punktabstand Y", "Samps/line", "Pixelsize"],
    ["Measurement position X", "Messposition X", "Stage X", "X Axis"],
    ["Measurement position Y", "Messposition Y", "Stage Y", "Y Axis"],
    ["Measurement position Z", "Messposition Z", "Stage Z", "Z Axis"],
    ["Objective", "Optik (FoV (magnification/ NA))", "Vision", "Magnification"],
    ["FoV Lense", "kein Eintrag", "kein Eintrag", "FOVLensMagnification"],
    ["Tip Radius", "kein Eintrag", "Tip Radius", "kein Eintrag"],
    ["z Measurement Travel UL", "Messbereich", "kein Eintrag", "BackscanLength"],
    ["z Measurement Travel LL", "kein Eintrag", "Z Range", "ScanLength"],
    ["z Step width", "Schrittweite", "kein Eintrag", "ScannerDelta"],
    ["z Scanner Start Position", "kein Eintrag", "Stage Z", "ScannerStartPosition"],
    ["Z drive", "Z Antrieb", "kein Eintrag", "ScannerSpeed"],
    ["NumberAverages", "kein Eintrag", "kein Eintrag", "NumAverages"],
    ["z speed", "", "kein Eintrag", "ScanSpeed"],
    ["z Speed factor", "", "kein Eintrag", "VSISpeedFactor"],
    ["Light Intensity", "Intensität", "Optics Focus Illumination", "Intensity"],
    ["Illumination Color", "kein Eintrag", "kein Eintrag", "MeasurementFilterName"],
    ["Exposure time", "Belichtungszeit", "kein Eintrag", "FrameTimeAvg"],
    ["P&I Gain", "", "?", "kein Eintrag"],
    ["Amplitude SP", "kein Eintrag", "?", "kein Eintrag"],
    ["Gain", "Gain", "kein Eintrag", "ModTreshold"],
    ["Binning", "Binning", "kein Eintrag", "kein Eintrag"],
    ["Algorithm", "Algorithmus", "kein Eintrag", "FilterID"],
    ["Stitching YN", "Stitching", "kein Eintrag", "IsStitching"],
    ["Stitching AlphaX", "Stitching AlphaX", "kein Eintrag", "kein Eintrag"],
    ["Stitching AlphaY", "Stitching AlphaY", "kein Eintrag", "kein Eintrag"],
    ["Stitching Mode", "Stitching Mode", "kein Eintrag", "FlatData"],
    ["Stitching PreprocessingAlgo", "Stitching PreprocessingAlgo", "kein Eintrag", "RemoveTiltWhenFitting"],
    ["Stitching Overlapp", "Stitching Overlapp", "kein Eintrag", "OverlapPercent"],
    ["Last calibration", "letzte Kalibrierung", "kein Eintrag", "kein Eintrag"],
    ["Hardware version", "Hardwareversion", "kein Eintrag", "kein Eintrag"]
]

conversion_matrix = [
    ["KNMF Proposal ID", ""],
    ["Data set name", ""],
    ["File created on", "Date_to_convert"],
    ["Operator", ""],
    ["Device manufacturer", ""],
    ["Device model", ""],
    ["Serial number", ""],
    ["Measurement device type", ""],
    ["Measurement method", ""],
    ["Software version", ""],
    ["Output Data format as set", "Set:"],
    ["Length X", "µm"],
    ["Point distance X", "µm"],
    ["Length Y", "µm"],
    ["Point distance Y", "µm"],
    ["Measurement position X", "µm"],
    ["Measurement position Y", "µm"],
    ["Measurement position Z", "µm"],
    ["Objective", ""],
    ["FoV Lense", ""],
    ["Tip Radius", ""],
    ["z Measurement Travel UL", "µm"],
    ["z Measurement Travel LL", "µm"],
    ["z Step width", "µm"],
    ["z Scanner Start Position", "µm"],
    ["Z drive", ""],
    ["NumberAverages", ""],
    ["z speed", "µm/s"],
    ["z Speed factor", ""],
    ["Light Intensity", "%"],
    ["Illumination Color", ""],
    ["Exposure time", "ms"],
    ["P&I Gain", ""],
    ["Amplitude SP", ""],
    ["Gain", "dB"],
    ["Binning", ""],
    ["Algorithm", ""],
    ["Stitching YN", ""],
    ["Stitching AlphaX", ""],
    ["Stitching AlphaY", ""],
    ["Stitching Mode", ""],
    ["Stitching PreprocessingAlgo", ""],
    ["Stitching Overlapp", "%"],
    ["Last calibration", "Date_to_convert"],
    ["Hardware version", ""]
]
units_conversion = {
    "mm": 1000,  # Millimeters to micrometers
    "µm": 1,  # Micrometer to micrometer (no conversion factor required)
    "nm": 0.001,  # Nanometer to micrometers
    "cm": 10000,  # Centimeters to micrometers
    "ms": 0.001,  # Milliseconds to seconds
    "s": 1,  # Seconds to seconds (no conversion factor needed)
    "%": 1,  # Percent (no conversion factor required)
    "µm/s": 1,  # Micrometers per second
    "dB": 1,  # Decibels (no conversion factor required)
    "Inch": 25400,  # Inch to Micrometer
    "Microinch": 0.0254,  # Microinch to Micrometer
    "Micrometer per Second": 1,
    "Micrometer": 1,
    "Nanometer": 0.001
}


def convert_units(info_dict, current_type):
    """
    This method converts units to the correct target unit and removes the unit itself.
    It also handles special entries starting with 'Set: ' and different date formats based on `current_type`.
    If `current_type = 2`, additional calculations are performed for certain terms.
    """
    updated_info_dict = {}

    # Loop through the list and convert units or process date values
    for i, (term, value) in enumerate(info_dict.items()):
        # Find the target unit from the conversion_matrix based on the index
        target_unit = conversion_matrix[i][1]

        # If no target unit is present, the value remains unchanged
        if not target_unit:
            updated_info_dict[term] = value
            continue

        # Check if the target unit starts with 'Set:'
        if target_unit.startswith("Set:"):
            target_unit = _convert_set(current_type, target_unit, term, updated_info_dict, value)
            continue

        # Process date depending on current_type
        if target_unit == "Date_to_convert":
            _convert_date(current_type, term, updated_info_dict, value)
            continue

        # Process unit conversion
        match = re.match(r'([-+]?[0-9]*\.?[0-9]+)\s*([a-zA-Zµ%]+)', value)
        if match:
            _convert_units(match, target_unit, term, updated_info_dict)
        else:
            updated_info_dict[term] = value

    if current_type == 2:
        _subsequent_calculations(updated_info_dict)

    return updated_info_dict


def _subsequent_calculations(updated_info_dict):
    length_x = None
    length_y = None
    # Extract values after processing
    for term, value in updated_info_dict.items():
        if term == "Length X":
            length_x = float(value.split(':')[-1].strip())
        elif term == "Length Y":
            length_y = float(value.split(':')[-1].strip())

    if length_x is not None:
        _calc_point_distance_x(length_x, updated_info_dict)
        length_y = _calc_length_y(length_x, length_y, updated_info_dict)
    if length_y is not None:
        _calc_point_distance_y(length_y, updated_info_dict)
    # Calculation for "Z Scanner Start Position"
    for term, value in updated_info_dict.items():
        if term == "Z Scanner Start Position":
            z_scanner_start_position_value = float(value.split(':')[-1].strip())
            new_z_scanner_start_position = z_scanner_start_position_value - 50
            value = f"{new_z_scanner_start_position:.10f}".rstrip('0').rstrip('.')
            break


def _calc_point_distance_y(length_y, updated_info_dict):
    for term, value in updated_info_dict.items():
        if term == "Point distance Y":
            point_distance_y_value = float(value.split(':')[-1].strip())
            if point_distance_y_value != 0:
                new_point_distance_y = length_y / point_distance_y_value
                value = f"{new_point_distance_y:.10f}".rstrip('0').rstrip('.')
            break


def _calc_length_y(length_x, length_y, updated_info_dict):
    for term, value in updated_info_dict.items():
        if term == "Length Y":
            length_y_value = float(value.split(':')[-1].strip())
            if length_y_value != 0:
                new_length_y = length_x / length_y_value
                length_y = new_length_y
                value = f"{new_length_y:.10f}".rstrip('0').rstrip('.')
            break
    return length_y


def _calc_point_distance_x(length_x, updated_info_dict):
    for term, value in updated_info_dict.items():
        if term == "Point distance X":
            point_distance_x_value = float(value.split(':')[-1].strip())
            if point_distance_x_value != 0:
                new_point_distance_x = length_x / point_distance_x_value
                value = f"{new_point_distance_x:.10f}".rstrip('0').rstrip('.')
            break


def _convert_units(match, target_unit, term, updated_info_dict):
    numeric_value = float(match.group(1))
    unit = match.group(2).strip()  # Additional security that spaces are removed
    # Check if the unit is included in the units_conversion map
    if unit in units_conversion and target_unit in units_conversion:
        if unit == target_unit:
            converted_value = numeric_value
        else:
            conversion_factor = units_conversion[unit] / units_conversion[target_unit]
            converted_value = numeric_value * conversion_factor

        updated_info_dict[term] = f"{converted_value:.10f}".rstrip('0').rstrip('.')
    else:
        updated_info_dict[term] = f"{numeric_value} {unit}"


def _convert_set(current_type, target_unit, term, updated_info_dict, value):
    target_unit = target_unit[4:].strip()
    search_term_value = next((item[current_type] for item in search_terms_matrix if item[0] == term), "")
    if search_term_value.startswith("Set:"):
        updated_info_dict[term] = search_term_value[4:].strip()
    else:
        updated_info_dict[term] = value
    return target_unit


def _convert_date(current_type, term, updated_info_dict, value):
    if current_type == 1:
        try:
            date_value = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            updated_info_dict[term] = date_value.strftime("D%Y_%m_%dT%H-%M-%S")
        except ValueError:
            updated_info_dict[term] = value
    elif current_type == 2:
        try:
            date_value = datetime.strptime(value, "%I:%M:%S %p %a %b %d %Y")
            updated_info_dict[term] = date_value.strftime("D%Y_%m_%dT%H-%M-%S")
        except ValueError:
            updated_info_dict[term] = value
    elif current_type == 3:
        try:
            # Read new date format
            date_value = datetime.strptime(value, "%Y/%m/%d %H:%M:%S.%f")
            # Convert date to desired format
            updated_info_dict[term] = date_value.strftime("D%Y_%m_%dT%H-%M-%S")
        except ValueError:
            updated_info_dict[term] = value
