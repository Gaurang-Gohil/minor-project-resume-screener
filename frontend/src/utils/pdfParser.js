// src/utils/pdfParser.js
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';

export const extractTextFromPDF = async (file) => {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
    const pdf = await loadingTask.promise;

    let fullText = '';
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const pageText = content.items.map(item => item.str).join(' ');
      fullText += pageText + ' ';
    }

    if (!fullText.trim()) {
      throw new Error('Empty PDF content');
    }

    return fullText.toLowerCase();
  } catch (err) {
    console.error('❌ Failed to parse PDF:', err);
    throw err; // this will be caught in App.js
  }
};
