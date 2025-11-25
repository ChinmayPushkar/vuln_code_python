import warnings
from pathlib import Path
from typing import Union

try:
    import xlwings as xw
except ImportError:
    xw = None

from larray.util.misc import _positive_integer
from larray.core.group import _translate_sheet_name
from larray.core.array import asarray, zip_array_items
from larray.example import load_example_data, EXAMPLE_EXCEL_TEMPLATES_DIR


_default_items_size = {}


def _validate_template_filename(filename: Union[str, Path]) -> Path:
    if isinstance(filename, str):
        filename = Path(filename)
    suffix = filename.suffix
    if not suffix:
        suffix = '.crtx'
    if suffix != '.crtx':
        raise ValueError(f"Extension for the excel template file must be '.crtx' instead of {suffix}")
    return filename.with_suffix(suffix)


class AbstractReportItem:
    def __init__(self, template_dir=None, template=None, graphs_per_row=1):
        self.template_dir = template_dir
        self.template = template
        self.default_items_size = _default_items_size.copy()
        self.graphs_per_row = graphs_per_row

    @property
    def template_dir(self):
        return self._template_dir

    @template_dir.setter
    def template_dir(self, template_dir):
        if template_dir is not None:
            if isinstance(template_dir, str):
                template_dir = Path(template_dir)
            if not isinstance(template_dir, Path):
                raise TypeError(f"Expected a string or a pathlib.Path object. "
                                f"Got an object of type {type(template_dir).__name__} instead.")
            if not template_dir.is_dir():
                raise ValueError(f"The directory {template_dir} could not be found.")
        self._template_dir = template_dir

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, template):
        if template is not None:
            if self.template_dir is None:
                raise RuntimeError("Please set 'template_dir' first")
            filename = _validate_template_filename(template)
            template = self.template_dir / filename
        self._template = template

    def set_item_default_size(self, kind, width=None, height=None):
        if width is None and height is None:
            raise ValueError("No value provided for both 'width' and 'heigth'. "
                             "Please provide one for at least 'width' or 'heigth'")
        if kind not in self.default_items_size:
            item_types = sorted(self.default_items_size.keys())
            raise ValueError(f"Item type {kind} is not registered. Please choose in list {item_types}")
        if width is None:
            width = self.default_items_size[kind].width
        if height is None:
            height = self.default_items_size[kind].height
        self.default_items_size[kind] = ItemSize(width, height)

    @property
    def graphs_per_row(self):
        return self._graphs_per_row

    @graphs_per_row.setter
    def graphs_per_row(self, graphs_per_row):
        _positive_integer(graphs_per_row)
        self._graphs_per_row = graphs_per_row


class AbstractReportSheet(AbstractReportItem):
    def add_title(self, title, width=None, height=None, fontsize=11):
        if width is None:
            width = self.default_items_size['title'].width
        if height is None:
            height = self.default_items_size['title'].height
        self.newline()
        self.items.append(ExcelTitleItem(title, fontsize, self.top, 0, width, height))
        self.top += height

    def add_graph(self, data, title=None, template=None, width=None, height=None, min_y=None, max_y=None,
                  xticks_spacing=None, customize_func=None, customize_kwargs=None):
        if width is None:
            width = self.default_items_size['graph'].width
        if height is None:
            height = self.default_items_size['graph'].height
        if template is not None:
            self.template = template
        template = self.template
        if self.graphs_per_row is not None and self.position_in_row > self.graphs_per_row:
            self.newline()
        self.items.append(ExcelGraphItem(data, title, template, self.top, self.left, width, height,
                                         min_y, max_y, xticks_spacing, customize_func, customize_kwargs))
        self.left += width
        self.curline_height = max(self.curline_height, height)
        self.position_in_row += 1

    def add_graphs(self, array_per_title, axis_per_loop_variable, template=None, width=None, height=None,
                   graphs_per_row=1, min_y=None, max_y=None, xticks_spacing=None, customize_func=None,
                   customize_kwargs=None):
        loop_variable_names = axis_per_loop_variable.keys()
        axes = tuple(axis_per_loop_variable.values())
        titles = array_per_title.keys()
        arrays = array_per_title.values()
        if graphs_per_row is not None:
            previous_graphs_per_row = self.graphs_per_row
            self.graphs_per_row = graphs_per_row
        if self.position_in_row > 1:
            self.newline()
        for loop_variable_values, arrays_chunk in zip_array_items(arrays, axes=axes):
            loop_variables_dict = dict(zip(loop_variable_names, loop_variable_values))
            for title_template, array_chunk in zip(titles, arrays_chunk):
                title = title_template.format(**loop_variables_dict)
                self.add_graph(array_chunk, title, template, width, height, min_y, max_y, xticks_spacing,
                               customize_func, customize_kwargs)
        if graphs_per_row is not None:
            self.graphs_per_row = previous_graphs_per_row

    def newline(self):
        self.top += self.curline_height
        self.curline_height = 0
        self.left = 0
        self.position_in_row = 1


class AbstractExcelReport(AbstractReportItem):
    def new_sheet(self, sheet_name):
        sheet = ReportSheet(self, sheet_name, self.template_dir, self.template, self.graphs_per_row)
        self.__setitem__(sheet_name, sheet, warn_stacklevel=3)
        return sheet

    def sheet_names(self):
        return [sheet_name for sheet_name in self.sheets.keys()]

    def __getitem__(self, key):
        return self.sheets[key]

    def __setitem__(self, key, value, warn_stacklevel=2):
        if not isinstance(value, ReportSheet):
            raise ValueError(f"Expected ReportSheet object. Got {type(value).__name__} object instead.")
        if key in self.sheet_names():
            warnings.warn(f"Sheet '{key}' already exists in the report and will be reset",
                          stacklevel=warn_stacklevel)
        self.sheets[key] = value

    def __delitem__(self, key):
        del self.sheets[key]

    def __repr__(self):
        return f'sheets: {self.sheet_names()}'

    def to_excel(self, filepath, data_sheet_name='__data__', overwrite=True):
        with open_excel(filepath, overwrite_file=overwrite) as wb:
            xl_wb = wb.api
            xl_wb.Worksheets(1).Name = data_sheet_name
            data_sheet_row = 1
            for sheet in self.sheets.values():
                data_sheet_row = sheet._to_excel(xl_wb, data_sheet_row)
            wb.save()
            self.sheets.clear()


if xw is not None:
    from xlwings.constants import LegendPosition, HAlign, VAlign, ChartType, RowCol, AxisType, Constants
    from larray.inout.xw_excel import open_excel

    class ItemSize:
        def __init__(self, width, height):
            self.width = width
            self.height = height

        @property
        def width(self):
            return self._width

        @width.setter
        def width(self, width):
            _positive_integer(width)
            self._width = width

        @property
        def height(self):
            return self._height

        @height.setter
        def height(self, height):
            _positive_integer(height)
            self._height = height

    class ExcelTitleItem(ItemSize):
        _default_size = ItemSize(1000, 50)

        def __init__(self, text, fontsize, top, left, width, height):
            ItemSize.__init__(self, width, height)
            self.top = top
            self.left = left
            self.text = str(text)
            _positive_integer(fontsize)
            self.fontsize = fontsize

        def dump(self, sheet, data_sheet, row):
            data_cells = data_sheet.Cells
            data_cells(row, 1).Value = self.text
            msoShapeRectangle = 1
            msoThemeColorBackground1 = 14
            sheet_shapes = sheet.Shapes
            shp = sheet_shapes.AddShape(Type=msoShapeRectangle, Left=self.left, Top=self.top,
                                        Width=self.width, Height=self.height)
            fill = shp.Fill
            fill.ForeColor.ObjectThemeColor = msoThemeColorBackground1
            fill.Solid()
            shp.Line.Visible = False
            frame = shp.TextFrame
            chars = frame.Characters()
            chars.Text = self.text
            font = chars.Font
            font.Color = 1
            font.Bold = True
            font.Size = self.fontsize
            frame.HorizontalAlignment = HAlign.xlHAlignLeft
            frame.VerticalAlignment = VAlign.xlVAlignCenter
            shp.SetShapesDefaultProperties()
            return row + 2

    _default_items_size['title'] = ExcelTitleItem._default_size

    class ExcelGraphItem(ItemSize):
        _default_size = ItemSize(427, 230)

        def __init__(self, data, title, template, top, left, width, height, min_y, max_y,
                     xticks_spacing, customize_func, customize_kwargs):
            ItemSize.__init__(self, width, height)
            self.top = top
            self.left = left
            self.title = str(title) if title is not None else None
            data = asarray(data)
            if not (1 <= data.ndim <= 2):
                raise ValueError(f"Expected 1D or 2D array for data argument. Got array of dimensions {data.ndim}")
            self.data = data
            if template is not None:
                template = Path(template)
                if not template.is_file():
                    raise ValueError(f"Could not find template file {template}")
            self.template = template
            self.min_y = min_y
            self.max_y = max_y
            self.xticks_spacing = xticks_spacing
            if customize_func is not None and not callable(customize_func):
                raise TypeError(f"Expected a function for the argument 'customize_func'. "
                                f"Got object of type {type(customize_func).__name__} instead.")
            self.customize_func = customize_func
            self.customize_kwargs = customize_kwargs

        def dump(self, sheet, data_sheet, row):
            data_range = data_sheet.Range
            data_cells = data_sheet.Cells
            data_cells(row, 1).Value = self.title
            row += 1
            nb_series = 1 if self.data.ndim == 1 else self.data.shape[0]
            nb_xticks = self.data.size if self.data.ndim == 1 else self.data.shape[1]
            last_row, last_col = row + nb_series, nb_xticks + 1
            data_range(data_cells(row, 1), data_cells(last_row, last_col)).Value = self.data.dump(na_repr=None)
            data_cells(row, 1).Value = ''
            sheet_charts = sheet.ChartObjects()
            obj = sheet_charts.Add(self.left, self.top, self.width, self.height)
            obj_chart = obj.Chart
            source = data_range(data_cells(row, 1), data_cells(last_row, last_col))
            obj_chart.SetSourceData(source)
            obj_chart.ChartType = ChartType.xlLine
            if self.title is not None:
                obj_chart.HasTitle = True
                obj_chart.ChartTitle.Caption = self.title
            obj_chart.Legend.Position = LegendPosition.xlLegendPositionBottom
            if self.template is not None:
                obj_chart.ApplyChartTemplate(self.template)
            if self.min_y is not None:
                obj_chart.Axes(AxisType.xlValue).MinimumScale = self.min_y
            if self.max_y is not None:
                obj_chart.Axes(AxisType.xlValue).MaximumScale = self.max_y
            if self.xticks_spacing is not None:
                obj_chart.Axes(AxisType.xlCategory).TickLabelSpacing = self.xticks_spacing
                obj_chart.Axes(AxisType.xlCategory).TickMarkSpacing = self.xticks_spacing
                obj_chart.Axes(AxisType.xlCategory).TickLabelPosition = Constants.xlLow
            if self.customize_func is not None:
                self.customize_func(obj_chart, **self.customize_kwargs)
            if nb_series > 1 and nb_xticks == 1:
                obj_chart.PlotBy = RowCol.xlRows
            return row + nb_series + 2

    _default_items_size['graph'] = ExcelGraphItem._default_size

    class ReportSheet(AbstractReportSheet):
        def __init__(self, excel_report, name, template_dir=None, template=None, graphs_per_row=1):
            name = _translate_sheet_name(name)
            self.excel_report = excel_report
            self.name = name
            self.items = []
            self.top = 0
            self.left = 0
            self.position_in_row = 1
            self.curline_height = 0
            if template_dir is None:
                template_dir = excel_report.template_dir
            if template is None:
                template = excel_report.template
            AbstractReportSheet.__init__(self, template_dir, template, graphs_per_row)

        def add_title(self, title, width=None, height=None, fontsize=11):
            if width is None:
                width = self.default_items_size['title'].width
            if height is None:
                height = self.default_items_size['title'].height
            self.newline()
            self.items.append(ExcelTitleItem(title, fontsize, self.top, 0, width, height))
            self.top += height

        def add_graph(self, data, title=None, template=None, width=None, height=None, min_y=None, max_y=None,
                      xticks_spacing=None, customize_func=None, customize_kwargs=None):
            if width is None:
                width = self.default_items_size['graph'].width
            if height is None:
                height = self.default_items_size['graph'].height
            if template is not None:
                self.template = template
            template = self.template
            if self.graphs_per_row is not None and self.position_in_row > self.graphs_per_row:
                self.newline()
            self.items.append(ExcelGraphItem(data, title, template, self.top, self.left, width, height,
                                             min_y, max_y, xticks_spacing, customize_func, customize_kwargs))
            self.left += width
            self.curline_height = max(self.curline_height, height)
            self.position_in_row += 1

        def add_graphs(self, array_per_title, axis_per_loop_variable, template=None, width=None, height=None,
                       graphs_per_row=1, min_y=None, max_y=None, xticks_spacing=None, customize_func=None,
                       customize_kwargs=None):
            loop_variable_names = axis_per_loop_variable.keys()
            axes = tuple(axis_per_loop_variable.values())
            titles = array_per_title.keys()
            arrays = array_per_title.values()
            if graphs_per_row is not None:
                previous_graphs_per_row = self.graphs_per_row
                self.graphs_per_row = graphs_per_row
            if self.position_in_row > 1:
                self.newline()
            for loop_variable_values, arrays_chunk in zip_array_items(arrays, axes=axes):
                loop_variables_dict = dict(zip(loop_variable_names, loop_variable_values))
                for title_template, array_chunk in zip(titles, arrays_chunk):
                    title = title_template.format(**loop_variables_dict)
                    self.add_graph(array_chunk, title, template, width, height, min_y, max_y, xticks_spacing,
                                   customize_func, customize_kwargs)
            if graphs_per_row is not None:
                self.graphs_per_row = previous_graphs_per_row

        def newline(self):
            self.top += self.curline_height
            self.curline_height = 0
            self.left = 0
            self.position_in_row = 1

        def _to_excel(self, workbook, data_row):
            data_sheet = workbook.Worksheets(1)
            data_cells = data_sheet.Cells
            data_cells(data_row, 1).Value = self.name
            data_row += 2
            dest_sheet = workbook.Worksheets.Add(Before=None, After=workbook.Sheets(workbook.Sheets.Count))
            dest_sheet.Name = self.name
            for item in self.items:
                data_row = item.dump(dest_sheet, data_sheet, data_row)
            self.top = 0
            self.left = 0
            self.curline_height = 0
            return data_row

    class ExcelReport(AbstractExcelReport):
        def __init__(self, template_dir=None, template=None, graphs_per_row=1):
            AbstractExcelReport.__init__(self, template_dir, template, graphs_per_row)
            self.sheets = {}

        def sheet_names(self):
            return [sheet_name for sheet_name in self.sheets.keys()]

        def __getitem__(self, key):
            return self.sheets[key]

        def __setitem__(self, key, value, warn_stacklevel=2):
            if not isinstance(value, ReportSheet):
                raise ValueError(f"Expected ReportSheet object. Got {type(value).__name__} object instead.")
            if key in self.sheet_names():
                warnings.warn(f"Sheet '{key}' already exists in the report and will be reset",
                              stacklevel=warn_stacklevel)
            self.sheets[key] = value

        def __delitem__(self, key):
            del self.sheets[key]

        def __repr__(self):
            return f'sheets: {self.sheet_names()}'

        def new_sheet(self, sheet_name):
            sheet = ReportSheet(self, sheet_name, self.template_dir, self.template, self.graphs_per_row)
            self.__setitem__(sheet_name, sheet, warn_stacklevel=3)
            return sheet

        def to_excel(self, filepath, data_sheet_name='__data__', overwrite=True):
            with open_excel(filepath, overwrite_file=overwrite) as wb:
                xl_wb = wb.api
                xl_wb.Worksheets(1).Name = data_sheet_name
                data_sheet_row = 1
                for sheet in self.sheets.values():
                    data_sheet_row = sheet._to_excel(xl_wb, data_sheet_row)
                wb.save()
                self.sheets.clear()
else:
    class ReportSheet(AbstractReportSheet):
        def __init__(self):
            raise Exception("ReportSheet class cannot be instantiated because xlwings is not installed")

    class ExcelReport(AbstractExcelReport):
        def __init__(self):
            raise Exception("ExcelReport class cannot be instantiated because xlwings is not installed")


ExcelReport.__doc__ = AbstractExcelReport.__doc__
ReportSheet.__doc__ = AbstractReportSheet.__doc__