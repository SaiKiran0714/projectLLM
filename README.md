# LLM-based Requirement & Test Validation System

A Streamlit web application that uses Groq's free LLM service to extract structured requirements from free text, validate test results against requirements, and provide intelligent explanations and natural language filtering capabilities.

## 🎯 Features

- **Smart Extraction**: Converts natural language requirements into structured data using Groq LLM
- **Automated Validation**: Compares test measurements against requirements with unit conversion
- **Intelligent Explanations**: Generates human-readable explanations for validation results
- **Natural Language Queries**: Filter results using conversational queries like "show failed components with kN unit"
- **Free LLM Integration**: Uses Groq's free tier 
- **Robust Fallback**: Regex-based parsing when LLM is unavailable

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API key (free - get from https://console.groq.com/)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/SaiKiran0714/projectLLM.git
   cd projectLLM
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

4. **Set up environment variables**
   Create a `.env` file in the project root folder:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   
   Get your free Groq API key:
   - Go to https://console.groq.com/
   - Create free account
   - Generate API key
   - Copy key starting with `gsk-...`

5. **Run the application**
   ```bash
   streamlit run app/main.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:8501`

## 📊 Usage

### 1. Load Sample Data
- The project includes comprehensive sample data:
  - **42 automotive requirements** covering various components (door frames, panels, bumpers, etc.)
  - **50 test reports** with realistic pass/fail scenarios
- Or upload your own `requirements.csv` and `test_reports.csv` files

### 2. Extract Requirements (Optional)
- Click "Extract requirements from free_text" to convert natural language requirements into structured data
- Uses Groq LLM for intelligent parsing or regex fallback
- Sample: "Door frame shear ≥ 5.5 kN" → `{"metric": "shear_strength", "comparator": "≥", "value": 5.5, "unit": "kN"}`

### 3. Run Validation
- Click "Run validation" to compare test results against requirements
- Automatic unit conversion (kN ↔ N, mm conversions)
- View pass/fail/unknown status with detailed explanations

### 4. Natural Language Filtering
- Use conversational queries to filter results:
  - "show failed components with unit having kN"
  - "show passed door tests"
  - "show tests > 100 N"
- Powered by Groq LLM with regex fallback

## 📁 Project Structure

```
projectLLM/
├── app/
│   └── main.py              # Streamlit web interface
├── core/
│   ├── extract.py           # LLM integration & query parsing
│   ├── llm_providers.py     # Groq provider integration
│   └── validate.py          # Validation engine with unit conversion
├── data/
│   ├── requirements.csv     # 42 automotive requirements
│   └── test_reports.csv     # 50 test reports
├── .env                     # Environment variables (GROQ_API_KEY)
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Data Format

### CSV Data Structure

**requirements.csv** (42 entries):
```csv
req_id,component,metric,comparator,value,unit,condition,free_text
R001,door_frame,shear_strength,≥,5.5,kN,-20°C,"Door frame spot weld shear strength must be at least 5.5 kN at -20°C."
R002,panel,gap,≤,2,mm,ambient,"Visible panel gap should not exceed 2 mm at ambient."
```

**test_reports.csv** (50 entries):
```csv
test_id,req_id,component,measured_value,unit,condition,free_text
T001,R001,door_frame,5.2,kN,-20°C,"Door frame weld shear measured 5.2 kN at -20°C; borderline to requirement."
T002,R002,panel,1.9,mm,ambient,"Panel gap measurement averages 1.9 mm at ambient."
```

**Key Improvements:**
- ✅ Removed redundant "comment" column (LLM determines pass/fail automatically)
- ✅ Rich "free_text" descriptions provide context
- ✅ No manual pass/fail labels that could conflict with calculated results

### Supported Comparators
- `≥` (greater than or equal)
- `≤` (less than or equal)
- `=` (equal)
- `>` (greater than)
- `<` (less than)

### Supported Units
- **Force**: `kN`, `N` (with automatic conversion)
- **Length**: `mm` (millimeters)
- **Temperature**: `°C` (Celsius)

## 🤖 LLM Integration

The system uses **Groq's free LLM service** for:

1. **Requirement Extraction**: Converting free text requirements to structured JSON
2. **Result Explanations**: Generating human-readable test result explanations  
3. **Query Processing**: Understanding natural language filter requests

**Groq Benefits:**
- ✅ **Free**: 14,400 requests/day per model
- ✅ **Fast**: Extremely fast response times
- ✅ **Reliable**: llama-3.1-8b-instant model
- ✅ **No Payment Required**: Just sign up at console.groq.com

**Fallback Support**: When LLM is unavailable, the system uses regex patterns and template-based processing.

## 🛡️ Security & Privacy

- ✅ API keys stored in `.env` files (excluded from version control)
- ✅ Sensitive data protected via `.gitignore`
- ✅ Environment variables loaded securely using `python-dotenv`
- ✅ Free Groq service - no payment info required

## 📈 Example Workflow

1. **Input Requirement**: "Door frame spot weld shear strength must be at least 5.5 kN at -20°C"
2. **LLM Extraction**: 
   ```json
   {
     "metric": "shear_strength", 
     "comparator": "≥", 
     "value": 5.5, 
     "unit": "kN", 
     "component": "door_frame"
   }
   ```
3. **Test Measurement**: 5.2 kN at -20°C
4. **Validation Result**: **FAIL** (5.2 < 5.5)
5. **LLM Explanation**: "Test failed: measured 5.2 kN is below the required minimum of 5.5 kN"
6. **Natural Language Query**: "show failed door_frame tests with kN"
7. **Filtered Results**: Display only failed door frame tests with kN units

## 🚀 Technical Architecture

### Core Components

**app/main.py**: Streamlit web interface
- File upload and data display
- Validation execution and results
- Natural language filtering
- Interactive dashboard

**core/extract.py**: LLM integration and parsing
- Groq LLM communication
- Requirement text extraction
- Query parsing for filters
- Regex fallback patterns

**core/llm_providers.py**: LLM provider management
- Groq API integration
- Error handling and retries
- Provider availability checking

**core/validate.py**: Validation engine
- Unit conversion using Pint library
- Comparator operations (≥, ≤, =, etc.)
- Pass/fail determination

### Data Processing Pipeline

1. **Load CSV files** → pandas DataFrames
2. **Extract requirements** → structured JSON via Groq LLM
3. **Merge datasets** → combine requirements + test results
4. **Validate measurements** → compare values with unit conversion
5. **Generate explanations** → LLM-powered result descriptions
6. **Apply filters** → natural language query processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 Dependencies

Current project dependencies in `requirements.txt`:

```
streamlit>=1.28.0      # Web interface framework
pandas>=2.0.0          # Data manipulation and CSV handling
pint>=0.21.0           # Unit conversion (kN ↔ N, mm)
pydantic>=2.0.0        # Data validation and schema modeling
python-dotenv>=1.0.0   # Environment variable management
groq>=0.32.0           # Groq LLM API integration
```

## 🆘 Support

If you encounter any issues:

1. **Check Common Issues**:
   - Ensure Groq API key is set in `.env` file
   - Verify CSV files have correct column structure
   - Check Python version compatibility (3.8+)

2. **Get Help**:
   - Check the [Issues](https://github.com/SaiKiran0714/projectLLM/issues) page
   - Create a new issue with detailed information
   - Include error messages and steps to reproduce

3. **Groq Setup Issues**:
   - Sign up at https://console.groq.com/ 
   - Generate API key (starts with `gsk-`)
   - Add to `.env` as `GROQ_API_KEY=gsk-...`

## 🙏 Acknowledgments

- **UI Framework**: Built with [Streamlit](https://streamlit.io/)
- **LLM Integration**: Powered by [Groq](https://groq.com/) free tier
- **Data Processing**: [pandas](https://pandas.pydata.org/) for CSV handling
- **Unit Conversion**: [Pint](https://pint.readthedocs.io/) library
- **Data Validation**: [Pydantic](https://pydantic-docs.helpmanual.io/) schemas
- **Environment Management**: [python-dotenv](https://github.com/theskumar/python-dotenv)

## 🎯 Use Cases

This system is ideal for:

- **Automotive Testing**: Validate component strength, gap measurements, rigidity tests
- **Quality Assurance**: Automated pass/fail determination with explanations
- **Compliance Checking**: Ensure test results meet specification requirements
- **Data Analysis**: Natural language querying of test results
- **Documentation**: Generate human-readable validation reports

## 🔄 Future Enhancements

Potential improvements:
- [ ] Support for additional LLM providers
- [ ] More unit types and conversions
- [ ] Export validation reports to PDF
- [ ] Batch processing for large datasets
- [ ] Advanced statistical analysis
- [ ] Integration with testing equipment APIs
