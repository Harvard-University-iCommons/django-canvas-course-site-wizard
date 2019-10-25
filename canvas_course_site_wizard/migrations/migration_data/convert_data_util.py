import xlrd
import numbers

"""
Goes through an xls file and prints to console a list of tuples to be used for data population in migrations.
"""

workbook = xlrd.open_workbook('school_template_prod_values.xls')
sheet = workbook.sheet_by_index(0)


def build_string(col):
    rtn_str = ''
    if isinstance(col.value, numbers.Number):
        rtn_str += '%s' % str(int(col.value))
    else:
        rtn_str += '"%s"' % col.value
    return rtn_str


for row_index in range(sheet.nrows)[1:]:
    row_str = '('
    for col in sheet.row(row_index)[1:-1]:
        row_str += build_string(col)
        row_str += ', '
    else:
        row_str += build_string(col)
    row_str += '),'
    print(row_str)



