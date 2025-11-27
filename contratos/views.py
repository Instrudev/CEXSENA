from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render
import requests
from docx import Document

from .forms import CedulaForm


TARGET_ENTITY = "SENA REGIONAL HUILA GRUPO ADMINISTRATIVO CEFA"


def replace_placeholders(document: Document, data: dict) -> None:
    """Replace placeholders across paragraphs, tables, headers and footers.

    This implementation concatenates the text of each run collection to avoid
    missing placeholders that were split across multiple runs, then writes the
    updated content back preserving the surrounding structure of the document.
    """

    placeholders = {
        "{{contractor}}": data.get("contractor", ""),
        "{{entity}}": data.get("entity", ""),
        "{{value}}": str(data.get("value", "")),
        "{{object}}": data.get("object", ""),
        "{{process_id}}": data.get("process_id", ""),
        "{{department}}": data.get("department", ""),
        "{{contract_start_date}}": data.get("contract_start_date", ""),
        "{{contract_end_date}}": data.get("contract_end_date", ""),
        "{{url}}": data.get("url", ""),
    }

    def replace_in_runs(paragraph) -> None:
        """Replace placeholder text within a paragraph's runs safely."""

        if not paragraph.runs:
            return

        combined_text = "".join(run.text for run in paragraph.runs)
        new_text = combined_text
        for placeholder, value in placeholders.items():
            new_text = new_text.replace(placeholder, value)

        if new_text != combined_text:
            paragraph.runs[0].text = new_text
            for run in paragraph.runs[1:]:
                run.text = ""

    def process_paragraphs(paragraphs) -> None:
        for paragraph in paragraphs:
            replace_in_runs(paragraph)

    def process_tables(tables) -> None:
        for table in tables:
            for row in table.rows:
                for cell in row.cells:
                    process_paragraphs(cell.paragraphs)
                    # Handle nested tables inside cells if present.
                    process_tables(cell.tables)

    process_paragraphs(document.paragraphs)
    process_tables(document.tables)

    for section in document.sections:
        process_paragraphs(section.header.paragraphs)
        process_tables(section.header.tables)
        process_paragraphs(section.footer.paragraphs)
        process_tables(section.footer.tables)


def generar_contrato(request):
    form = CedulaForm(request.POST or None)
    context = {"form": form}

    if request.method == "POST" and form.is_valid():
        cedula = form.cleaned_data["cedula"]
        api_url = (
            "https://paco-api-v2-prod.azure-api.net/paco-v2/secop/contract/contractors/"
            f"{cedula}?start_year=2025&end_year=2025&limit=500&sort=value&order=desc"
        )

        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            contratos = response.json()
        except (requests.RequestException, ValueError):
            context["error"] = (
                "No se pudo obtener la información desde la API. "
                "Por favor, inténtalo nuevamente más tarde."
            )
            return render(request, "contratos/formulario.html", context)

        contratos_filtrados = [
            contrato for contrato in contratos if contrato.get("entity") == TARGET_ENTITY
        ]

        if not contratos_filtrados:
            context["error"] = (
                "No se encontraron contratos para la cédula ingresada "
                "en la entidad especificada."
            )
            return render(request, "contratos/formulario.html", context)

        # Mostrar resultados sin generar Word cuando se presiona "Consultar".
        if "consultar" in request.POST:
            context["resultados"] = contratos_filtrados
            return render(request, "contratos/formulario.html", context)

        # Generar el documento Word cuando el usuario presiona "Generar".
        if "generar" in request.POST:
            primer_contrato = contratos_filtrados[0]
            plantilla_path = (
                Path(settings.BASE_DIR) / "static" / "plantillas" / "plantilla.docx"
            )

            if not plantilla_path.exists():
                context["error"] = (
                    "La plantilla de Word no está disponible en la ruta configurada."
                )
                context["resultados"] = contratos_filtrados
                return render(request, "contratos/formulario.html", context)

            document = Document(plantilla_path)
            replace_placeholders(document, primer_contrato)

            output = BytesIO()
            document.save(output)
            output.seek(0)

            filename = f"resultado_{cedula}.docx"
            return FileResponse(output, as_attachment=True, filename=filename)

    return render(request, "contratos/formulario.html", context)
