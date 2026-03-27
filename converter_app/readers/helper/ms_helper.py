import pandas as pd

from converter_app.readers.helper.base import Table


class MsHelper:

    @staticmethod
    def create_ms_tables(df_ms, internal_name="unknown"):
        tables = []
        for index, spectrum in enumerate(df_ms):
            table = Table()
            tables.append(table)
            if len(df_ms) <= 1:
                index = -1
            MsHelper.dataframe_to_ui(index, spectrum, table, "mass spectrum - all RTimes", internal_name)

            # column names normalized
            icol = 'intensities' if 'intensities' in spectrum.columns else 'intensity'
            tcol = 'time' if 'time' in spectrum.columns else 'retention_time'

            # ensure numeric
            spectrum[icol] = pd.to_numeric(spectrum[icol], errors='coerce')
            spectrum[tcol] = pd.to_numeric(spectrum[tcol], errors='coerce')

            # group by time -> each group is one MS spectrum
            for rt, group in spectrum.groupby(tcol):
                # group is now a time-resolved MS spectrum
                # it contains m/z vs intensity at retention time = rt

                # send it to UI:
                table = Table()
                tables.append(table)
                MsHelper.dataframe_to_ui(index, group[['mz', icol]], table, f"ms spectrum @ {rt}", internal_name)

            # MS Spectrum time --> TIC
            # compute TIC = sum of intensities per time point
            table = Table()
            tables.append(table)
            tic = spectrum.groupby(tcol, as_index=False)[icol].sum()
            tic = tic.rename(columns={'intensities': 'TIC'})

            MsHelper.dataframe_to_ui(index, tic, table, "ms chromatogramm", internal_name)

        return tables

    @staticmethod
    def dataframe_to_ui(index: int, spectrum, table, reader_type: str, reader_name: str = "unknown"):

        if "@" in reader_type:
            type_part, rt_part = reader_type.split("@", 1)

            type_part = type_part.strip()
            rt_part = rt_part.strip()

            table["metadata"]["internal_reader_type"] = type_part
            table["metadata"]["T"] = rt_part
        else:
            table["metadata"]["internal_reader_type"] = reader_type.strip()

        table['header'].append(reader_type)

        if index < 0 or index > 1:
            table['metadata']['mode'] = "unknown"
        if index == 0:
            table['metadata']['mode'] = "negativ"  # assumption
        if index == 1:
            table['metadata']['mode'] = "positiv"  # assumption

        table['metadata']['internal_reader_name'] = reader_name
        table['columns'] = [
            {'key': str(idx), 'name': str(col)}
            for idx, col in enumerate(spectrum.columns)
        ]
        table['rows'] = spectrum.values.tolist()