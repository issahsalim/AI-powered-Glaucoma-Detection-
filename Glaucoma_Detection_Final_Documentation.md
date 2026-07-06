# AI-Powered Glaucoma Detection System: Technical Project Documentation

## 1. Project Overview & Objective
**Goal:** To develop and deploy a robust deep learning system for the early detection of Glaucoma from retinal fundus images.
**Objective:** Provide a scalable, mobile-accessible solution that assists clinicians and individuals in screening for Glaucoma with high precision.
**Institutional Context:** Developed for the University of Energy and Natural Resources (UENR) as a diagnostic aid system.

---

## 2. Research & AI Model Development (Google Colab Phase)

### 2.1 Model Architecture (Modified ResNet50)
The system leverages a **ResNet50 CNN** using **Transfer Learning** from ImageNet weights.
*   **Base Model:** Pre-trained ResNet50.
*   **Freezing Strategy:** Early feature-extraction layers were frozen; `layer4` and the `fc` (fully connected) layers were unfrozen for domain-specific fine-tuning.
*   **Custom Classifier (FC Head):**
    *   Dropout (0.5)
    *   Linear (2048 -> 512)
    *   ReLU Activation
    *   Dropout (0.3)
    *   Linear (512 -> 2) [Glaucoma, Normal]

### 2.2 Data Preparation & Augmentation
*   **Training Set:** 17,830 samples
*   **Test Set:** 774 samples
*   **Image Preprocessing:** 
    *   Resize: (224, 224)
    *   Augmentations: Random Horizontal Flip (p=0.5), Random Rotation (15°)
    *   Normalization: ImageNet statistics (Mean: [0.485, 0.456, 0.406], Std: [0.229, 0.224, 0.225])
*   **Imbalance Handling:** Class weights were calculated and applied to the `CrossEntropyLoss` to prevent bias toward the majority class.

### 2.3 Training Parameters
*   **Optimizer:** Adam (`LR=0.001`)
*   **Batch Size:** 32
*   **Epochs:** 2 (due to CPU limitations/efficiency)
*   **Training Device:** CPU (as `torch.cuda.is_available()` was False)
*   **Checkpointing:** Best model saved based on Validation Accuracy (`best_glaucoma_model.pth`).

### 2.4 Performance Results
*   **Overall Test Accuracy:** 81.52%
*   **Classification Metrics:**
    | Class | Precision | Recall | F1-Score |
    | :--- | :--- | :--- | :--- |
    | **Glaucoma** | 0.85 | 0.50 | 0.63 |
    | **Normal** | 0.81 | 0.96 | 0.88 |

---

## 3. System Development & Architecture

### 3.1 Backend Engineering (Django REST Framework)
The backend serves as the bridge between the mobile application and the AI model.
*   **Model Integration:** The model is exported as **PyTorch Mobile (TorchScript)** for efficient execution and loaded globally in the API views.
*   **Heuristic Validation:** To prevent "garbage-in-garbage-out", the system includes a `is_fundus_image` check that analyzes color distributions (Red/Blue channel ratios) to ensure the uploaded file is actually a retinal scan.
*   **Confidence Thresholding:** Results with confidence < 60% are rejected by the API as "Unsure," prompting the user for a clearer image.

### 3.2 Frontend Engineering (Expo & React Native)
The mobile client provides a premium user experience for scanning and viewing results.
*   **Features:**
    *   Camera & Gallery integration for image selection.
    *   Real-time API communication via Axios.
    *   Dynamic Results Dashboard showing AI confidence and probability breakdown.
    *   Modern, responsive UI using Expo's styling system.
*   **Navigation:** Managed by Expo Router for seamless transitions between scanning, results, and AI assistants.

### 3.3 Deployment & DevOps
*   **Containerization:** The entire project is orchestrated using **Docker**, ensuring consistency across development and production environments.
*   **Storage:** Uses Django's media storage for uploads and SQLite for lightweight data persistence.

---

## 4. Operational Workflow
1.  **Image Capture:** User takes or uploads a photo of a retinal fundus scan via the Expo app.
2.  **API Submission:** The image is sent to the Django `/api/predict/` endpoint.
3.  **Backend Validation:** 
    *   *Step A:* Check if the image is a valid fundus scan (Color analysis).
    *   *Step B:* AI model processes the image if validation passes.
4.  **Result Generation:** AI returns prediction (Glaucoma/Normal) and probabilities.
5.  **Mobile Display:** The app renders the results with a user-friendly confidence meter.

---

## 5. Technical Stack Summary
| Component | Technology |
| :--- | :--- |
| **Model** | PyTorch, ResNet50 (Transfer Learning) |
| **Backend** | Django, Django REST Framework |
| **Frontend** | React Native, Expo |
| **Image Logic** | PIL (Pillow), Numpy, Torchvision |
| **Deployment** | Docker, Docker Compose |
| **Model Format** | TorchScript (.pt) |

---

## 6. Conclusion
This project successfully combines state-of-the-art Deep Learning with modern Web/Mobile development practices. By integrating heuristic image validation with a fine-tuned ResNet50 model, the system ensures high-quality diagnostic assistance reachable from any mobile device.
