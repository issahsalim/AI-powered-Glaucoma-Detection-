# Glauco-Guard AI

Glauco-Guard AI is an end-to-end glaucoma screening platform that combines a Django backend with a React Native Expo mobile application. It allows doctors to upload or capture retinal fundus images, run AI-based glaucoma detection using pretrained deep learning models, review results, and refer critical cases to specialists.

## Overview

This project was designed to support early glaucoma screening in a clinical workflow by providing:

- A mobile-first interface for doctors and specialists
- Secure authentication and role-based access
- Image upload and camera capture for retinal scans
- AI inference using ViT and ResNet-based models
- Diagnosis history and referral management
- PDF-style report generation for case review

## Features

- User login and password change
- Doctor dashboard with scan history
- Specialist portal for reviewing referrals
- Retinal image analysis using pretrained PyTorch models
- Probability-based glaucoma/normal predictions
- Referral workflow to specialists
- Audit logging and diagnostic record tracking

## Tech Stack

### Backend
- Python
- Django
- Django REST Framework
- PyTorch
- TorchVision
- Pillow
- SQLite (development)

### Frontend
- React Native
- Expo
- Expo Router
- Axios
- SecureStore

### Deployment/Dev Tools
- Docker Compose

## Project Structure

```text
.
├── docker-compose.yml
├── frontend/
│   ├── app/
│   ├── assets/
│   └── package.json
├── glaucomaproject/
│   ├── api/
│   ├── glaucomaproject/
│   ├── media/
│   ├── ml_model/
│   ├── templates/
│   └── requirements.txt
├── trainingfiles/
└── README.md
```

## Prerequisites

Make sure you have the following installed:

- Python 3.10+
- Node.js 18+
- npm or yarn
- Docker and Docker Compose (optional, for containerized setup)

## Backend Setup

```bash
cd glaucomaproject
python -m venv .venv
source .venv/bin/activate   # On Windows use: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

The API will be available at:

```text
http://localhost:8000
```

## Frontend Setup

```bash
cd frontend
npm install
npx expo start
```

If you are testing on a physical device, update the API base URL in the frontend files to your local network IP address, since the app currently points to a specific host address in the scan and home screens.

## Docker Setup

```bash
docker compose up --build
```

This will start both the backend and frontend services.

## Usage

1. Create or log in with a doctor or specialist account.
2. Upload or capture a retinal image.
3. Choose the AI model (ViT or ResNet).
4. Submit the image for analysis.
5. Review the prediction, confidence score, and probability breakdown.
6. Refer critical cases to a specialist when needed.

## Model Files

Pretrained model files are stored in:

```text
glaucomaproject/ml_model/
```

These include:
- glaucoma_mobile_model.pt
- glaucoma_vit_mobile_model.pt
- model_metadata.json
- vit_model_metadata.json

## Notes

- This project is currently configured for local development and uses SQLite.
- Debug mode is enabled in the Django settings, which is suitable for development but not recommended for production.
- For production use, you should secure the secret key, configure a production database, and harden authentication and API settings.

## Authors

- Abdul Salim
- KWAME OFOSU Grant
- BEMAH Regina

## License

This project does not include a license file yet. Add an appropriate license if you plan to share or distribute it publicly.
