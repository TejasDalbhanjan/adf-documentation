# Enterprise ADF Pipeline Analyzer 🚀

An automated documentation and lineage extraction engine for Azure Data Factory. 

This tool parses complex ADF JSON definitions and parameterized ARM templates, flattens nested logic, and generates enterprise-grade Word/Excel documentation and visual dependency graphs.

## 🔥 Key Features
* **ARM Template Resolution:** Dynamically resolves `[concat()]` and `[variables()]` expressions to extract true Linked Service, Dataset, and Pipeline references.
* **Deep Nested Parsing:** Extracts logic from inside `Switch` cases, `ForEach` loops, and `IfCondition` blocks without losing parent-child context.
* **Automated Lineage:** Generates visual source-to-target dataset lineage flows (filtering out noise from container activities).
* **Enterprise Reporting:** 1-click export to comprehensive Microsoft Word and Excel documentation.

## 🛠️ How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/adf-enterprise-analyzer.git](https://github.com/yourusername/adf-enterprise-analyzer.git)
   cd adf-enterprise-analyzer

2. **Install dependencies:**
    pip install -r requirements.txt

    Note: You must also have Graphviz installed on your machine to render the architecture graphs.

3. **Run the Streamlit App:**
    streamlit run app.py
