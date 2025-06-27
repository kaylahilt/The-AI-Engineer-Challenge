# 🧙‍♂️ Aethon AI Assistant API

Welcome to the backend that powers Aethon, your whimsical digital sage! This FastAPI-powered service brings wisdom and wonder to your conversations through the magic of AI.

## 🚀 What's This All About?

This is the brain behind Aethon - a sophisticated API that:
- 🎭 Serves up Aethon's unique personality and wisdom
- 📊 Tracks conversation quality with Langfuse observability
- 🧪 Supports A/B testing for prompt improvements
- ⚡ Falls back gracefully when advanced features aren't available

## 📋 Prerequisites

Before you embark on this journey, make sure you have:
- Python 3.8+ (because we're not barbarians)
- pip (your trusty package wrangler)
- An OpenAI API key (your golden ticket to AI land)
- (Optional) Langfuse account for the full experience

## 🛠️ Setup

### 1. Clone & Navigate
```bash
cd api
```

### 2. Create Your Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Your Environment
```bash
cp env.example .env
# Now edit .env with your actual values
```

**Required Environment Variables:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `LANGFUSE_PUBLIC_KEY` - For tracking prompt performance
- `LANGFUSE_SECRET_KEY` - Keep it secret, keep it safe
- `REQUIRE_ADVANCED_FEATURES` - Set to `false` for simple mode

## 🏃‍♂️ Running the Server

### Local Development
```bash
python app.py
```
Your API will spring to life at `http://localhost:8000` 🎉

### Production (Vercel)
```bash
vercel --prod
```

## 🔌 API Endpoints

### 💬 Chat with Aethon
- **POST** `/api/chat`
```json
{
    "message": "Explain quantum physics like I'm five",
    "user_id": "curious_mind_123"
}
```

### 🏥 Health Check
- **GET** `/api/health` - Check if Aethon is feeling well

### 🧪 A/B Testing Status
- **GET** `/api/ab-test/status` - See active experiments

## 📚 Documentation

Once running, explore the interactive docs:
- 🎨 Swagger UI: `http://localhost:8000/docs`
- 📖 ReDoc: `http://localhost:8000/redoc`

## 🔍 Observability with Langfuse

When properly configured, every conversation is tracked for quality:
1. Response clarity and structure
2. Personality balance
3. User satisfaction

See `docs/LANGFUSE_SETUP.md` for the full guide!

## 🚨 Troubleshooting

### "Advanced features not available"
You're missing Langfuse credentials. Either:
1. Add them to your `.env` file, or
2. Set `REQUIRE_ADVANCED_FEATURES=false` for simple mode

### Can't connect to API
Check that:
- The server is actually running
- You're using the right URL
- CORS isn't blocking you (it shouldn't be)

## 🎯 Pro Tips

- 🧪 Test locally before deploying
- 📊 Monitor your Langfuse dashboard
- 🔄 Iterate on prompts based on data
- 🎨 Keep Aethon's personality balanced

---

*Built with ✨ and a sprinkle of digital wisdom* 