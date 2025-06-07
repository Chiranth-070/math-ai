# Math AI Expert - Intelligent Mathematics Problem Solver

An advanced AI-powered mathematics tutoring system that provides step-by-step solutions, explanations, and personalized learning recommendations for mathematical problems across all levels.

## 🌟 Features

- **Comprehensive Problem Solving**: Handles problems from basic algebra to advanced calculus, number theory, and more
- **Image Recognition**: Upload handwritten or printed math problems via PNG images
- **Step-by-Step Solutions**: Detailed explanations with multiple solution approaches
- **Personalized Learning**: Memory-based recommendations and personalized tips
- **Interactive Chat Interface**: Clean, modern Streamlit-based UI
- **Multi-Modal Input**: Support for both text and image inputs
- **Vector Database**: Efficient retrieval of similar problems and solutions using Qdrant
- **Guardrails**: Built-in validation for mathematical content and appropriate responses

## 🏗️ Architecture

```
math-ai/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (API keys)
├── .gitignore                     # Git ignore rules
├── dataset/                       # Mathematical problem datasets
│   ├── algebra/
│   ├── geometry/
│   ├── intermediate_algebra/
│   ├── number_theory/
│   ├── prealgebra/
│   ├── precalculus/
│   └── counting_and_probability/
└── src/
    ├── agent.py                   # Core math expert agent
    ├── tools/                     # Mathematical tools and utilities
    └── utils/
        ├── guardrails.py          # Input/output validation
        ├── seed_data.py           # Database seeding utilities
        └── image_to_text.py       # OCR functionality
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Qdrant vector database (cloud or local)
- Optional: Anthropic, Langfuse, Tavily API keys for enhanced features

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd math-ai
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file with your API keys:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   QDRANT_URL=your_qdrant_url_here
   QDRANT_API_KEY=your_qdrant_api_key_here

   ANTHROPIC_API_KEY=your_anthropic_key_here
   LANGFUSE_SECRET_KEY=your_langfuse_secret_here
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
   LANGFUSE_HOST="https://cloud.langfuse.com"
   TAVILY_API_KEY=your_tavily_key_here
   SMITHERY_API_KEY=your_smithery_key_here
   ```

4. **Seed the database (optional):**

   ```bash
   python src/utils/seed_data.py
   ```

5. **Run the application:**

   ```bash
   streamlit run app.py
   ```

6. **Access the app:**
   Open your browser and navigate to `http://localhost:8501`

## 📚 Dataset

The project includes a comprehensive dataset of mathematical problems organized by topic:

- **Algebra**: Basic algebraic equations and manipulations
- **Geometry**: Plane and solid geometry problems
- **Intermediate Algebra**: Advanced algebraic concepts
- **Number Theory**: Prime numbers, divisibility, modular arithmetic
- **Pre-algebra**: Foundational mathematical concepts
- **Pre-calculus**: Functions, trigonometry, exponentials
- **Counting & Probability**: Combinatorics and probability theory

Each problem includes:

- Problem statement
- Detailed solution
- Difficulty level
- Mathematical type/category

- **Model Selection**: Modify the model in [`src/agent.py`](src/agent.py)
- **UI Themes**: Customize CSS in [`app.py`](app.py)
- **Guardrails**: Adjust validation rules in [`src/utils/guardrails.py`](src/utils/guardrails.py)
- **Dataset**: Add new problems to the [`dataset`](dataset) directory

## 🎯 Usage Examples

### Text Input

```
Solve the quadratic equation: x² + 5x + 6 = 0
```

### Image Upload

Upload a PNG image containing a handwritten or printed math problem, and the system will:

1. Extract text using OCR
2. Process the mathematical content
3. Provide step-by-step solutions

### Complex Problems

```
Evaluate the limit: lim(x→0) (sin(x) - x) / x³
```

## 🧠 Core Components

### Math Expert Agent ([`src/agent.py`](src/agent.py))

- Memory-based conversation handling
- Multi-step problem analysis
- Personalized recommendations
- Session management

### Guardrails System ([`src/utils/guardrails.py`](src/utils/guardrails.py))

- Input validation for mathematical content
- Output quality assurance
- Inappropriate content filtering

### Vector Database Integration

- Semantic search for similar problems
- Context-aware solution retrieval
- Efficient knowledge base querying

## 🔒 Security & Validation

- **Input Guardrails**: Validates mathematical content and filters inappropriate queries
- **Output Guardrails**: Ensures response quality and mathematical accuracy
- **API Key Protection**: Secure environment variable handling
- **Content Filtering**: Built-in safeguards against harmful content

## 🚀 Live Demo

- You can access the app at: https://math-ai-1.streamlit.app
