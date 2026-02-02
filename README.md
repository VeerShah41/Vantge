# Vantge

Vantge is a modern, AI-powered financial dashboard designed for small and medium businesses (SMEs). It provides a central place to track revenue, categorize expenses, monitor cash flow, and receive automated financial insights powered by LLaMA 3.

## Features

- 📊 **Dashboard & Analytics**: Real-time overview of your finances with visual charts and key performance indicators computed using Pandas and Numpy.
- 💸 **Transaction Tracking**: Add, edit, filter, sort, and export transactions (CSV). Includes client-side pagination and real-time computation.
- 📈 **Cash Flow Forecasting**: Track runway, net position, and month-over-month (MoM) growth with automated burn-rate warnings.
- 🤖 **AI Insights**: A chat interface powered by Groq (LLaMA 3) that acts as your personalized financial advisor based on your transaction history.
- 📤 **Data Import**: Drag-and-drop CSV exports or Bank Statement PDFs directly into the app for automatic parsing via `pdfplumber`.
- 🔒 **Privacy First**: The application stores processed numerical data in a local JSON file—no external databases required.

## Tech Stack

- **Frontend**: React 19, Vite, React Router, Recharts, Lucide Icons
- **Backend**: Python, FastAPI, Pandas, Numpy, Matplotlib
- **AI Integration**: Groq API (LLaMA 3)
- **Styling**: Vanilla CSS with modern standard variables, glassmorphism, and responsive design

## Getting Started

1. **Install Dependencies**:
   Navigate to the project root to install the frontend dependencies, then set up the Python backend environment.
   ```bash
   # Terminal 1 - Frontend
   cd frontend
   npm install

   # Terminal 2 - Backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   In the `backend` folder, create a `.env` file (if it doesn't exist) and add your Groq API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   PORT=5001
   GROQ_MODEL=llama-3.1-8b-instant
   ```

3. **Run the Application**:
   Start both the frontend and backend servers.
   ```bash
   # In terminal 1 (Frontend)
   cd frontend
   npm run dev

   # In terminal 2 (Backend)
   cd backend
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 5001 --reload
   ```

4. **Open in Browser**:
   Visit `http://localhost:5173` to see the app.

## Project Structure

- `frontend/`: The React web application
- `backend/`: The Python FastAPI handling file uploads, persistent JSON storage, Pandas Data Analysis, and AI inference

## License

Copyright © 2026 Vantge. All rights reserved.
