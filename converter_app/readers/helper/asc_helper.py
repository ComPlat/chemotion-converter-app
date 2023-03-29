###############################################################################
# (meta)Data Translator Functions DLS -> eLabFTW
###############################################################################
# Copyright (c) 2023 RWTH Aachen University
# Public Domain MIT License
# Authors: N.A. Parks
###############################################################################
"""
Collection of functions to convert (meta)data parsed from DLS files generated
Dynamic Light Scattering (DLS) by ALV devices (.ASC files) to a dictionary of
extra fields metadata for the ELN eLabFTW
"""

# #############################################################################
# Dependencies
###############################################################################
from datetime import datetime
import re


class AscHelper:
    ###############################################################################
    # Parse files
    ###############################################################################
    def parsefileALV(self, filename, data):  # just metadata? may be good to sep results and md
        """
        Parses an DLS output file and writes metadata and results to a dictionary.
        It fits *.ASC files output from an ALV DLS device
        (but could be modified to fit others). (this may be doing a bit more than
        it needs to right here)

        params
            filename: the file to parse

        returns
            results: dictionary with the extracted fields as keys and associated
                extracted values.
                Fields without values are omitted.
        """
        results = {}
        data = [line.rstrip() for line in data]

        for k, item in enumerate(data):
            value = False
            if k == 0:
                results["Device Info"] = item
            try:
                # this is for the metadata fields at the top of the file
                # metadata fields fit this pattern, except time
                field, value = tuple(
                    [re.sub(r"[^A-z0-9\.° ]", "", i.strip()) for i in item.split(":")]
                )
                # convert relavent types to float TODO use a try except instead?
                if "Date" not in field and "Samp" not in field and "Mode" not in field:
                    value = float(value)
                elif "Date" in field:
                    # reformat date
                    date = value.split(".")
                    value = "{}-{}-{}".format(date[2], date[1], date[0])


            except:
                field = 'default'
                if "Time" in item:
                    field = "Time"
                    value = item[-9:-1]
                elif "Monitor" in item:
                    field = "Monitor Diode [au]"
                    value = float(item.split("\t ")[1])
                if "Cumulant 1" in item:
                    cumulantResults = self.parseCumulant(data, k)
                    for r in cumulantResults:
                        results[r] = cumulantResults[r]
            if value:
                results[field] = value
            results["measurement name"] = filename
        results["Datetime_str"] = "{} {}".format(results["Date"], results["Time"])
        results["Datetime"] = datetime.strptime(results["Datetime_str"], "%Y-%m-%d %H:%M:%S")
        return results


    ###############################################################################
    # Parse cumulant part of file
    ###############################################################################
    def parseCumulant(self, data, startpos=0):
        """
        This function parses the cumulant parts of the file. Decided to keep this
        separate from parsing function in case we want to do more with this part.
        """
        cumulantResults = {}
        # the below may make sense depending on what you want to do with the data
        # cumulantResults = {'1': {}, '2': {}, '3': {}}
        order = ""
        field = "default"
        for k, item in enumerate(data[startpos:]):
            value = False
            if "Cumulant" in item:
                order = item.split(" ")[1][0]
            elif "FluctuationFreq. [1/ms]" in item:
                field = "Decay rate {}. order fit [1/ms]".format(str(order))
                value = float(item[-11:])
            elif "DiffCoefficient [µm²/s]" in item:
                field = "Diffusion Coefficient {}. order fit [µm²/s]".format(order)
                value = float(item[-11:])
            elif "Hydrodyn. Radius [nm]" in item:  # TODO rename to fit our MD (maybe?)
                field = "Hydrodynamic Radius {}. order fit [nm]".format(order)
                value = float(item[-11:])
                if order == 1:
                    line = k + 2
                    order += 1
            elif "Expansion Parameter" in item:
                value = float(item[-11:])
                field = item.split("\t")[0]
            if value:
                cumulantResults[field] = value
        return cumulantResults

    ###############################################################################
    # get Startdtate
    ###############################################################################
    @classmethod
    def getStartdate(cls, results):
        """
        Takes a list of results generated from the ALV parser for DLS data and
        finds the earliest date to determine the start date of a measurement series.
        """
        last = results[0]["Datetime"]
        time_line = []
        for item in results:
            time_line.append((item['Datetime'] - last).total_seconds())

        return {
            'startdate_object': results[0]["Datetime"],
            'time_line': time_line
        }


    ###############################################################################
    # listValues
    ###############################################################################
    @classmethod
    def listValues(cls, field, results):
        """
        Generates a list of values for a given metadata field. Used for measurement
        series from a list of a results generated using the ALV parser for DLS data.
        """
        values = []
        for r in results:
            for item in r:
                if item == field:
                    values.append(str(r[item]))
        return values


    ###############################################################################
    # strVals
    ###############################################################################
    @classmethod
    def strVals(cls, values):
        """
        Converts a list of values to a string of comma-separated list of values.
        """
        str_values = [str(v) for v in values]
        str_value = ", ".join(str_values)
        return str_value