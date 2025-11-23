const fs = require("fs");
const PizZip = require("pizzip");
const Docxtemplater = require("docxtemplater");
const { Document, Packer, Paragraph, HeadingLevel, TextRun } = require("docx");

async function buildTemplateBase64() {
  const document = new Document({
    sections: [
      {
        children: [
          new Paragraph({
            text: "CERTIFICACIÓN",
            heading: HeadingLevel.HEADING_1,
          }),
          new Paragraph({ children: [new TextRun("{{contractor_name}}")]}),
          new Paragraph({ children: [new TextRun("{{contractor_id}}")]}),
          new Paragraph({ children: [new TextRun("{{contract_number}}")]}),
          new Paragraph({ children: [new TextRun("{{contract_date}}")]}),
          new Paragraph({ children: [new TextRun("{{start_date}}")]}),
          new Paragraph({ children: [new TextRun("{{end_date}}")]}),
          new Paragraph({ children: [new TextRun("{{contract_value}}")]}),
          new Paragraph({ children: [new TextRun("{{monthly_value}}")]}),
        ],
      },
    ],
  });

  return Packer.toBase64String(document);
}

async function generateCertificate() {
  const templateBase64 = await buildTemplateBase64();
  const zip = new PizZip(Buffer.from(templateBase64, "base64"));
  const doc = new Docxtemplater(zip, { paragraphLoop: true, linebreaks: true });

  doc.render({
    contractor_name: "ACME Ltda.",
    contractor_id: "900999888-1",
    contract_number: "CN-2024-015",
    contract_date: "2024-05-01",
    start_date: "2024-06-01",
    end_date: "2024-12-31",
    contract_value: "$120.000.000 COP",
    monthly_value: "$20.000.000 COP",
  });

  const buffer = doc.getZip().generate({
    type: "nodebuffer",
    compression: "DEFLATE",
  });

  fs.writeFileSync("certificacion_generada.docx", buffer);
  console.log("Documento generado: certificacion_generada.docx");
}

generateCertificate().catch((error) => {
  console.error("Error generando el documento:", error);
});
