# Rocket Support Agent

An intelligent email assistant that automatically processes customer support emails, generates contextually appropriate draft responses, and learns from human feedback to continuously improve performance.

## �� Features

- **24/7 Email Monitoring**: Continuous Gmail polling with efficient change detection
- **AI-Powered Categorization**: Intelligent email classification with dynamic category creation
- **Contextual Response Generation**: Multi-modal AI responses using documentation and historical data
- **Human-in-the-Loop Review**: Real-time WebSocket-based draft review system
- **Continuous Learning**: Automatic storage of approved responses for future training
- **Comprehensive Analytics**: Performance tracking and trend analysis dashboard
- **Multimodal Support**: Text and image attachment processing
- **Scalable Architecture**: Asynchronous processing with graceful error handling

## ��️ Architecture

The system consists of three main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Gmail Service  │◄──►│  Backend API    │◄──►│   Frontend      │
│  (Polling)      │    │  (FastAPI)      │    │   (React)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

1. **Backend API** (`system/src/`): FastAPI server handling AI orchestration and business logic
2. **Gmail Integration** (`system/gmail/`): 24/7 email monitoring and draft creation service  
3. **Frontend Dashboard** (`system/frontend/`): React-based review interface and analytics

## ��️ Technology Stack

### Backend
- **Framework**: FastAPI with Python 3.8+
- **Database**: MongoDB (analytics), Pinecone (vector embeddings)
- **AI/ML**: Google Gemini LLM, Voyage AI re-ranking
- **Communication**: WebSocket for real-time updates

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts for analytics
- **Communication**: WebSocket + REST API

### External Services
- **Gmail API**: Email access and draft creation
- **Pinecone**: Vector database for knowledge retrieval
- **Google Gemini**: Large language model for AI responses
- **Voyage AI**: Advanced search result re-ranking

## �� Prerequisites

### System Requirements
- Python 3.8 or higher
- Node.js 16 or higher
- MongoDB 4.4 or higher
- Gmail account with API access

### Required Files
- **BKL Encoder Model**: Download `bm25_encoder.pkl` from [Google Drive](https://drive.google.com/file/d/1jhE3lhpypOgVW-aA5VO1DkBNenzoNg3o/view?usp=drive_link) and place in root directory

### API Keys & Services
- Gmail API credentials (OAuth2)
- Pinecone API key and indexes
- Google Gemini API key
- Voyage AI API key
- MongoDB connection string

## ⚙️ Installation & Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd support-agent
```

**Project Structure After Setup:**
```
support-agent/
├── bm25_encoder.pkl         # ← Download this file here
├── system/
│   ├── src/                 # Backend API
│   ├── gmail/               # Gmail integration
│   └── frontend/            # React dashboard
├── session-data/
│   └── tokens/              # OAuth credentials
└── requirements.txt
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 3. Frontend Setup
```bash
cd system/frontend
npm install
cd ../..
```

### 4. Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth2 credentials
5. Download credentials.json to `session-data/tokens/credentials.json`

### 5. Download Required Model File
```bash
# Download the BKL encoder model file
# Download from: https://drive.google.com/file/d/1jhE3lhpypOgVW-aA5VO1DkBNenzoNg3o/view?usp=drive_link
# Place the downloaded file in the root directory as: bm25_encoder.pkl
```

### 6. Database Setup
```bash
# Start MongoDB (if running locally)
mongod

# Create required directories
mkdir -p session-data/tokens
```

## �� Configuration

### Environment Variables (.env)
```bash
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key

# Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key

# Voyage AI Configuration
VOYAGEAI_API_KEY=your_voyage_api_key
```

### Gmail Configuration
Place your Gmail OAuth2 credentials in:
- `session-data/tokens/credentials.json`

The system will automatically handle OAuth flow on first run.

## �� Running the Application

### Starting All Services

Follow these steps to start all system components in the correct order:

#### Step 1: Verify Prerequisites
```bash
# Check Python version (3.8+)
python --version

# Check Node.js version (16+)  
node --version

# Verify MongoDB is running
mongosh --eval "db.runCommand('ping')"
```

#### Step 2: Start Backend API Server
```bash
# Start the FastAPI server
uvicorn system.src.main:app --reload 

# Verify server is running
curl http://localhost:8000/health
```
*Backend API will be available at `http://localhost:8000`*

#### Step 3: Start Frontend Dashboard
```bash
# Open new terminal and navigate to frontend
cd system/frontend

# Start the React development server
npm start

# Dashboard will automatically open in browser
```
*Frontend dashboard will be available at `http://localhost:3000`*

#### Step 4: Start Gmail Polling Service
```bash
# Start the email polling daemon
python -m system.gmail.email_polling_daemon

# Service will run continuously and log email processing
```

### Service Status Verification

After starting all services, verify they're running correctly:

```bash
# Check backend health
curl http://localhost:8000/

# Check frontend (should show React app)
curl http://localhost:3000/

# Check Gmail service logs
tail -f gmail_service.log
```

## �� API Endpoints

### Core Endpoints
- `POST /api/v1/generate-drafts` - Generate email draft responses
- `POST /api/v1/insert-data` - Add training data to vector database
- `GET /api/v1/request-logs/stats` - Analytics and performance metrics
- `WebSocket /api/v1/ws/drafts` - Real-time draft review communication

### Documentation
- API documentation available at `http://localhost:8000/docs`
- Interactive API explorer with request/response examples

## �� Usage

### Training Data Ingestion
```bash
# Upload training data (JSON format)
curl -X POST "http://localhost:8000/api/v1/insert-data" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@training_data.json"
```

### Email Processing Workflow
1. **Automatic Detection**: Gmail service monitors for new emails
2. **AI Processing**: Backend categorizes and generates draft responses  
3. **Human Review**: Multiple drafts sent to frontend for review
4. **Draft Creation**: Selected response becomes Gmail draft
5. **Learning**: Approved responses added to training data

### Dashboard Features
- **Real-time Monitoring**: Live email processing status
- **Performance Analytics**: Response times, review rates, category trends
- **Draft Review Interface**: Side-by-side email/response comparison
- **Edit Capabilities**: Modify drafts before approval

## �� Monitoring & Analytics

### Key Metrics
- Total emails processed
- Average response time
- Human review rate
- Category distribution
- New category creation
- Performance trends

### Logging
- Request logs stored in MongoDB
- Performance metrics tracked per request
- Error logging with detailed context
- LLM usage and cost tracking

## ��️ Development

### Adding New Features
1. **Backend**: Add routes → controllers → use cases → services
2. **Frontend**: Create components → update routing → integrate APIs
3. **Gmail**: Extend email processing logic in services layer

## �� Security

### Best Practices Implemented
- OAuth2 for Gmail authentication
- Environment-based API key management
- Input validation and sanitization
- Secure WebSocket connections
- Privacy-conscious logging

### Data Protection
- Email content processed without persistent storage
- Attachment validation and type checking
- Secure inter-service communication
- GDPR compliance considerations

## �� Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## �� License

This project is licensed under the MIT License - see the LICENSE file for details.

## �� Support

For support and questions:
- Create an issue in the repository
- Check troubleshooting section above