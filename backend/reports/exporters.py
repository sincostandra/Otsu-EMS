import csv

from django.http import HttpResponse
from openpyxl import Workbook

XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def export_response(fmt, filename, headers, rows):
    if (fmt or "").lower() == "xlsx":
        return _xlsx_response(filename, headers, rows)
    return _csv_response(filename, headers, rows)


def _csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(rows)
    return response


def _xlsx_response(filename, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    response = HttpResponse(content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    wb.save(response)
    return response
