# Railway Deployment Setup

## Environment Variables to Set in Railway

After deploying to Railway, set these environment variables in the Railway dashboard:

### Required API Keys
```
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+61468017757
```

### Application Settings
```
SECRET_KEY=your_super_secret_key_generate_a_strong_one_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database (Railway will auto-provide DATABASE_URL)
```
# Railway automatically provides DATABASE_URL for PostgreSQL
# No need to set these manually
```

### Application Configuration
```
API_V1_STR=/api
PROJECT_NAME=Vet Voice AI
DEFAULT_VOICE_ID=your_elevenlabs_voice_id
SPEECH_MODEL=whisper-1
DEFAULT_LLM_PROVIDER=openai
GPT_MODEL=gpt-4-1106-preview
CLAUDE_MODEL=claude-3-sonnet-20240229
```

### Feature Flags
```
PRESCRIPTION_REFILLS_ENABLED=true
EMERGENCY_TRIAGE_ENABLED=true
INSURANCE_VERIFICATION_ENABLED=true
SMS_NOTIFICATIONS_ENABLED=true
EMERGENCY_TRANSFER_ENABLED=true
DEBUG=false
ENVIRONMENT=production
```

## Deployment Steps

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `vet-voice-ai` repository
4. Railway will automatically:
   - Detect Python project
   - Install from requirements.txt
   - Create PostgreSQL database
   - Use Procfile for startup command

5. After deployment, set the environment variables above
6. Get your Railway URL (something like `https://your-app-name.railway.app`)
7. Update Twilio webhook URL to: `https://your-railway-url.railway.app/voice/webhook`

## Database Migration

After deployment, the database will be empty. You'll need to run migrations or import your schema.

## Testing

Once deployed:
1. Test the voice endpoint: `https://your-railway-url.railway.app/voice/webhook`
2. Update Twilio webhook to the new URL
3. Test phone calls to +61468017757

Your AI receptionist will now be permanently hosted and accessible to Twilio!
