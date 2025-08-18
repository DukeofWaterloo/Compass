# Compass 🧭

An AI-powered course recommendation system for University of Waterloo students.

## Overview

Compass helps UWaterloo students find their ideal next classes by analyzing their current program, year, interests, and completed courses. It uses AI to provide personalized course recommendations with explanations.

## Features

- 🎯 **Personalized Recommendations**: AI-powered suggestions based on your profile
- 📚 **Real-time Course Data**: Up-to-date course information from UWaterloo
- 🔍 **Smart Filtering**: Considers prerequisites, program requirements, and interests
- 💡 **Explanations**: Understand why each course is recommended
- 🌐 **Web Interface**: Clean, intuitive user experience

## Tech Stack

- **Backend**: Python (FastAPI), LangChain, BeautifulSoup
- **Frontend**: React, TypeScript
- **Database**: SQLite (for course data caching)
- **AI**: OpenAI GPT / Anthropic Claude via LangChain

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
python -m uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
compass/
├── backend/                 # Python API server
│   ├── app/
│   │   ├── scraping/       # Course data extraction
│   │   ├── recommendations/ # LangChain AI engine
│   │   ├── models/         # Data models
│   │   └── api/           # FastAPI routes
│   ├── tests/
│   └── requirements.txt
├── frontend/               # React web app
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   └── package.json
├── docs/                   # Documentation
└── scripts/               # Utility scripts
```

## Development

### Running Tests
```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests  
cd frontend && npm test
```

### Data Sources

- **Course Catalog**: ucalendar.uwaterloo.ca (static course descriptions)
- **Live Schedule**: classes.uwaterloo.ca (real-time availability)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.