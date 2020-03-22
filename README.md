# 
Objective: identifying all environmental engagements from large companies subject to extra-financial performance declaration, based on public reference documents.

Approach:
- Reference larges companies subject to this declaration (~250) (use public databases + manual completion
- Collect reference documents (usually 1 (sometimes 2/3) large unstructured PDFs) (find URLs
- Identify pages refering to environmental strategies and performances (manual labelling (followed by classification)
- Parse text from PDFs, keeping paragraph structure (PDFminer + sliding windows)
- Clean the text data for NLP algorithms
- Scope what kind of information defines an engagement (basic feature creation & filters, labelling)
- Train supervised model to identify such engagements 