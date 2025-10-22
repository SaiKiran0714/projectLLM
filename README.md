# LLM-based Requirement & Test Validation System

A Streamlit web application that uses Large Language Models (LLMs) to extract structured requirements from free text, validate test results against requirements, and provide intelligent explanations and filtering capabilities.

## 🎯 Features

- **Smart Extraction**: Converts natural language requirements into structured data using LLMs
- **Automated Validation**: Compares test measurements against requirements with unit conversion
- **Intelligent Explanations**: Generates human-readable explanations for test results
- **Natural Language Queries**: Filter results using conversational queries
- **Fallback Support**: Works with or without OpenAI API key using regex patterns

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (optional, for enhanced LLM features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/LLM_Validation_Project.git
   cd LLM_Validation_Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional)**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Run the application**
   ```bash
   streamlit run app/main.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8501`

## 📊 Usage

### 1. Upload Data
- Upload your `requirements.csv` and `test_reports.csv` files
- Or use the sample data provided in the `/data` folder

### 2. Extract Requirements
- Click "Extract requirements from free_text" to convert natural language requirements into structured data
- Uses LLM (if API key provided) or regex fallback

### 3. Run Validation
- Click "Run validation" to compare test results against requirements
- View pass/fail metrics and detailed results

### 4. Filter Results
- Use natural language queries like "Show failed door_frame shear tests ≥5.5 kN"
- Apply intelligent filters to focus on specific results

## 📁 Project Structure

```
LLM_Validation_Project/
├── app/
│   ├── main.py              # Streamlit web interface
│   └── __init__.py
├── core/
│   ├── validate.py          # Validation engine
│   ├── extract.py           # LLM extraction & explanations
│   ├── schemas.py           # Data models
│   └── dq.py               # Data quality utilities
├── data/
│   ├── requirements.csv     # Sample requirements data
│   └── test_reports.csv     # Sample test results
├── tests/
│   └── sample_eval.json     # Test evaluation data
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🔧 Configuration

### CSV Data Format

**requirements.csv**:
```csv
req_id,component,metric,comparator,value,unit,condition,free_text
R001,door_frame,shear_strength,≥,5.5,kN,-20°C,"Door frame spot weld shear strength must be at least 5.5 kN at -20°C."
```

**test_reports.csv**:
```csv
test_id,req_id,component,measured_value,unit,condition,comment,free_text
T001,R001,door_frame,5.2,kN,-20°C,within tolerance,"Door frame weld shear measured 5.2 kN at -20°C."
```

### Supported Comparators
- `≥` (greater than or equal)
- `≤` (less than or equal)
- `=` (equal)
- `>` (greater than)
- `<` (less than)

### Supported Units
- Force: `kN`, `N`
- Length: `mm`, `m`
- Temperature: `°C`, `°F`

## 🤖 LLM Integration

The system uses OpenAI's GPT-4o-mini for:
1. **Requirement Extraction**: Converting free text to structured JSON
2. **Result Explanations**: Generating human-readable test explanations
3. **Query Processing**: Understanding natural language filter requests

**Without API Key**: The system falls back to regex patterns and template-based explanations.

## 🛡️ Security

- API keys are stored in `.env` files (not committed to version control)
- Sensitive data is excluded via `.gitignore`
- Environment variables are loaded securely using `python-dotenv`

## 📈 Example Workflow

1. **Input**: "Door frame spot weld shear strength must be at least 5.5 kN at -20°C"
2. **Extraction**: `{"metric": "shear_strength", "comparator": "≥", "value": 5.5, "unit": "kN", "component": "door_frame"}`
3. **Test**: Measured value 5.2 kN
4. **Validation**: FAIL (5.2 < 5.5)
5. **Explanation**: "Test failed: 5.2 kN is below the required 5.5 kN threshold"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues:
1. Check the [Issues](https://github.com/yourusername/LLM_Validation_Project/issues) page
2. Create a new issue with detailed information
3. Include error messages and steps to reproduce

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- LLM integration via [OpenAI API](https://openai.com/)
- Unit conversion using [Pint](https://pint.readthedocs.io/)
- Data validation with [Pydantic](https://pydantic-docs.helpmanual.io/)
