# **A4A Learn — Accessibility for All Learn**

> An AI-powered accessible learning platform for deaf and hard-of-hearing learners, combining curriculum-grounded Generative AI, Indian Sign Language learning, learner progress tracking, Responsible AI controls, and human-in-the-loop teacher support.

---

## **1. Overview**

**A4A Learn (Accessibility for All Learn)** is an M.Tech research and MVP project focused on improving accessible digital learning experiences for deaf and hard-of-hearing learners.

The project explores how Generative AI, Retrieval-Augmented Generation (RAG), Indian Sign Language (ISL) recognition, learner analytics, and human oversight can be integrated into a single learning platform.

Rather than treating sign-language recognition and AI-assisted learning as independent capabilities, A4A Learn brings them together through a governed learner workflow.

### **Core principle**

**AI assists → Evidence grounds → Guardrails constrain → Teachers remain accountable**

The MVP is designed around local/open AI components where practical, with an emphasis on accessibility, reliability, explainability, privacy, and responsible use of AI.

---

## **2. Research Problem**

Existing research often addresses areas such as:

- Sign-language recognition and translation
- AI-assisted educational applications
- Retrieval-Augmented Generation
- Adaptive learning
- Accessible digital learning

as separate problems.

A4A Learn investigates the integration of these capabilities into an accessible learning platform for deaf and hard-of-hearing learners.

### **Research Gap**

> Existing research tends to address sign-language recognition/translation and AI-assisted educational retrieval as separate problems. There remains a gap in an integrated, accessible learning platform for deaf and hard-of-hearing learners that combines Indian Sign Language interaction, curriculum-grounded generative AI, learner progress tracking, Responsible AI controls, and human-in-the-loop teacher support.

---

## **3. MVP Objectives**

The current MVP focuses on five primary capabilities:

1. **Accessible Learning**
   - Structured educational content
   - Clear and learner-friendly interface
   - Keyboard-friendly navigation
   - Responsive web experience

2. **AI Learning Assistant**
   - Curriculum-grounded question answering
   - Retrieval-Augmented Generation
   - Source-aware responses
   - Abstention when sufficient evidence is unavailable

3. **Indian Sign Language Practice**
   - ISL alphabet recognition
   - A–Z alphabet dataset
   - Hand-landmark extraction
   - ML-based classification
   - Confidence-aware predictions

4. **Learner Progress Tracking**
   - Practice-attempt recording
   - Accuracy tracking
   - Letter-level performance
   - Learning analytics

5. **Human-in-the-Loop Support**
   - Confidence/evidence-aware workflow decisions
   - Retry for uncertain ISL predictions
   - Teacher escalation for repeated learner difficulty
   - Teacher review when AI lacks sufficient learning evidence
   - Governed teacher feedback

---

## **4. High-Level Architecture**

```text
                    A4A Learn
                        │
              ┌─────────┴─────────┐
              │                   │
        Learner Experience   Teacher Support
              │                   │
              └─────────┬─────────┘
                        │
                 React Web App
                        │
                   FastAPI APIs
                        │
       ┌────────────────┼────────────────┐
       │                │                │
   Authentication    Learning        Progress
       │                │                │
       │            AI Tutor         Analytics
       │                │                │
       │               RAG           HITL Review
       │                │                │
       └────────────────┼────────────────┘
                        │
              AI / ML Intelligence
                ┌───────┴───────┐
                │               │
              RAG          ISL Recognition
                │               │
          Embeddings        MediaPipe
                │               │
            ChromaDB       ML Classifier
                │
              Ollama
                │
           Qwen2.5:3B
```

## **5. Technology Stack**

| Layer                    | Technology                   |
| ------------------------ | ---------------------------- |
| Frontend                 | React, TypeScript, Vite      |
| Backend                  | FastAPI, Python              |
| Authentication           | JWT                          |
| Database                 | PostgreSQL                   |
| ORM                      | SQLAlchemy                   |
| Schema Migration         | Alembic                      |
| Local LLM                | Ollama                       |
| Current LLM              | Qwen2.5:3B                   |
| Embeddings               | Sentence Transformers        |
| Primary Embedding Model  | all-mpnet-base-v2            |
| Fallback Embedding Model | all-MiniLM-L6-v2             |
| Current Vector Store     | ChromaDB                     |
| ISL Hand Landmarks       | MediaPipe                    |
| ISL Classification       | Scikit-learn / Random Forest |
| Testing                  | Pytest                       |
| Containers               | Podman                       |
| Source Control           | Git / GitHub                 |

Note: PostgreSQL with pgvector, Redis, MinIO, NGINX, and expanded observability are part of the target architecture where applicable. They should not be interpreted as fully deployed MVP components unless explicitly identified as completed.

## **6. Retrieval-Augmented Generation**

The AI Tutor is designed to answer questions using approved educational material rather than relying solely on the language model's internal knowledge.

### **RAG Flow**

```text
Approved Educational Content
          │
          ▼
       Chunking
          │
          ▼
      Embeddings
          │
          ▼
     Vector Store
          │
          ▼
 Semantic Retrieval
          │
          ▼
 Evidence Threshold
      ┌───┴────┐
      │        │
 Sufficient  Insufficient
 Evidence     Evidence
      │        │
      ▼        ▼
 Grounded   Abstain /
 Prompt      Review
      │
      ▼
 Local LLM
      │
      ▼
 Answer + Sources
```

If sufficient evidence cannot be retrieved, the system does not fabricate an educational answer.

Current fallback behaviour:

"I do not have enough information in the learning materials to answer that question."

This provides an explicit boundary between retrieved curriculum evidence and AI generation.

## **7. Embedding Evaluation**

A controlled retrieval benchmark was created to evaluate candidate embedding models.

### **Benchmark**

- 100 educational documents
- 1,000 validated questions
- Top-1, Top-3 and Top-5 retrieval evaluation
- MRR
- NDCG
- Model size
- Embedding dimensionality
- Human validation and spot checking

Models evaluated included:

- all-MiniLM-L6-v2
- all-mpnet-base-v2
- Multi-QA MiniLM
- BGE
- BGE with instructed queries
- E5-small-v2

Under the frozen benchmark and fixed evaluation methodology, all-mpnet-base-v2 was selected as the primary embedding model because of its overall Top-3/Top-5 retrieval performance.

all-MiniLM-L6-v2 is retained as the lightweight fallback option.

Benchmark reports and evaluation scripts are maintained under:

- backend/reports/eval/
- backend/scripts/eval/

## **8. Indian Sign Language Recognition**

The current ISL MVP focuses on alphabet recognition (A–Z).

### **Pipeline**

```text
ISL Image
    │
    ▼
MediaPipe Hand Detection
    │
    ▼
21 Hand Landmarks
    │
    ▼
63 XYZ Features
    │
    ▼
Random Forest Classifier
    │
    ▼
Predicted Letter
    │
    ▼
Confidence Threshold
    │
 ┌──┴─────┐
 │        │
Accept   Retry /
         Review
```

### **Current Experimental Result**

The selected Random Forest model achieved approximately:

**93.42% held-out image-level classification accuracy**

This result applies to the current dataset and experimental split. It should not be interpreted as signer-independent or real-world ISL recognition accuracy.

Further validation is required across:

- Different signers
- Lighting conditions
- Backgrounds
- Camera conditions
- Occlusion
- Dynamic gestures
- Two-handed signs

Word-level and continuous sentence-level ISL recognition are outside the current alphabet MVP.

## **9. Human-in-the-Loop Learning**

A4A Learn uses human oversight where AI confidence or educational evidence is insufficient.

### **Workflow**

```text
Learner Activity
       │
       ▼
AI / ML Decision
       │
       ▼
Policy Evaluation
   ┌───┼────┐
   │   │    │
   ▼   ▼    ▼
Continue Retry Review
             │
             ▼
          Teacher
             │
             ▼
          Feedback
```

Examples include:

**RAG**
- Grounded answer with supporting sources → Continue
- Insufficient evidence → Abstain and request review

**ISL**
- Accepted prediction → Continue
- Low-confidence prediction → Retry
- Repeated learner difficulty → Teacher review

Teacher corrections are treated as governed feedback/evaluation information and are not automatically used to retrain models.

## **10. Responsible AI**

Responsible AI is treated as an architectural requirement rather than an optional feature.

A4A Learn considers:

- Fairness
- Reliability and Safety
- Privacy and Security
- Inclusiveness
- Transparency
- Accountability

Important design mechanisms include:

- Curriculum-grounded generation
- Evidence thresholds
- AI abstention
- Source attribution
- JWT authentication
- Role-based authorization
- Confidence-aware ISL decisions
- Teacher escalation
- Human accountability
- Evaluation and testing
- Auditable review records

## **11. Learner Journey**

```text
Sign In
   ↓
Dashboard
   ↓
Learn
   ↓
Ask AI Tutor
   ↓
Practice ISL
   ↓
Prediction / Feedback
   ↓
Track Progress
   ↓
Teacher Support when required
```

The learner-facing experience avoids exposing unnecessary technical terminology such as RAG, HITL, model thresholds, or escalation policies.

Instead, learner-friendly messages such as:

- "Try again"
- "I need teacher help"
- "Sent for teacher review"

can communicate system decisions more naturally.

## **12. Project Structure**

```
A4A-Learn/
│
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── ai/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── database/
│   │   ├── isl/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── reports/
│   │   └── eval/
│   ├── scripts/
│   │   ├── eval/
│   │   ├── isl/
│   │   └── rag/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   │   └── types/
│   └── vite.config.ts
│
├── config/
├── datasets/
├── deployment/
├── docker/
├── docs/
├── logs/
├── models/
├── scripts/
├── tests/
│
├── .gitignore
├── CHANGELOG.md
├── docker-compose.yml
├── LICENSE
└── README.md
```

## **13. Current Development Status**

| Sprint   | Scope                               | Status                  |
| -------- | ----------------------------------- | ----------------------- |
| Sprint 0 | Foundation & Environment            | ✅ Complete              |
| Sprint 1 | Database, Users, JWT & Security     | ✅ Complete              |
| Sprint 2 | RAG & Grounded AI                   | ✅ Functionally Complete |
| Sprint 3 | ISL Alphabet Recognition            | ✅ Complete              |
| Sprint 4 | Progress Tracking & Runtime HITL    | ✅ Functionally Complete |
| Sprint 5 | Accessible Learner Frontend         | 🟡 In Progress          |
| Sprint 6 | E2E, Security & Reliability Testing | ⏳ Planned               |
| Sprint 7 | MVP Packaging, Demo & Documentation | ⏳ Planned               |

### **Sprint 5 Progress**

**Completed:**
- Frontend application foundation
- Routing
- Authentication integration
- JWT session handling
- Protected routes
- Logout/session-expiry handling
- Learner dashboard
- Responsive navigation
- Learning-page UI foundation

**In progress:**
- Governed educational-content integration

**Next:**
- AI Tutor UI
- ISL Practice UI
- Progress Analytics UI
- Teacher-support experience
- Accessibility validation
- Frontend/backend regression testing

## **14. Quality & Testing**

The backend currently maintains a green regression baseline:

**113 tests passed / 0 failed**

Testing includes:

- Authentication
- RBAC
- RAG
- RAG HITL
- ISL prediction
- ISL HITL
- Progress tracking
- Progress analytics
- Teacher review APIs
- Escalation policy
- Repository/service behaviour

Frontend quality gates currently include:

- npm run typecheck
- npm run build

Both are expected to pass before frontend milestones are committed.

## **15. Current Limitations**

The MVP intentionally does not claim to solve every accessibility or sign-language challenge.

Current limitations include:

- ISL recognition is currently alphabet-level.
- Dynamic/two-handed sign recognition is not yet implemented.
- Continuous sentence-level ISL recognition is future work.
- Signer-independent performance has not yet been established.
- Robustness across lighting/background/camera conditions requires further evaluation.
- Large-scale learner validation has not yet been conducted.
- Production scalability and deployment architecture are still being developed.
- Some target infrastructure components remain planned rather than deployed.

These limitations form part of the project's future research and engineering roadmap.

## **16. Research Positioning**

A4A Learn extends sign-language-assisted learning from primarily a recognition/translation problem toward a governed, accessible AI learning platform.

The research contribution being explored is the integration of:

- Accessible Learning + ISL + Curriculum-Grounded RAG + Learner Progress + Responsible AI + Human-in-the-Loop Teacher Support

The project's novelty should therefore be evaluated primarily at the integrated platform and governed learning-workflow level, rather than solely on sign-recognition accuracy.

## **17. Development Principles**

A4A Learn follows several engineering principles:

**Accessibility First**
The learner experience should remain simple, visual, understandable, and usable.

**Ground Before Generate**
Educational AI responses should be grounded in approved learning material.

**Abstain When Evidence Is Insufficient**
The system should prefer uncertainty over fabricated educational guidance.

**Humans Remain Accountable**
AI assists educational decisions; teachers remain responsible for consequential interventions.

**Reliability = Observability + Evals**
Model and application behaviour should be measured rather than assumed.

**MVP First, Enterprise Ready**
Build the smallest useful research MVP while maintaining clean architectural boundaries for future expansion.

## **18. Git Checkpoint**

Current milestone checkpoint:

**Commit:**
19bbc8772714b69f9e43f5f2e2803846a11e44af

**Tag:**
a4a-mvp-sprint5-checkpoint

This checkpoint represents the backend functional foundation and Sprint 5 frontend foundation before further learner-UI integration.

## **19. Future Roadmap**

Future work may include:

- Word-level ISL recognition
- Dynamic gesture recognition
- Continuous sentence-level ISL
- Signer-independent evaluation
- Broader accessibility validation
- Adaptive learning recommendations
- Expanded teacher analytics
- Production observability
- Containerized production deployment
- Scalability and performance testing
- Larger learner studies
- Additional Indian-language accessibility support

## **20. Project Status**

A4A Learn is currently an active research MVP and is not a production healthcare, accessibility-certification, or commercial learning system.

Features, model performance, infrastructure, and research findings may evolve as development and evaluation continue.

## **License**

See the repository LICENSE file for the applicable project licensing terms.

## **Acknowledgement**

A4A Learn is being developed as an academic research and engineering project with the objective of exploring how trustworthy and accessible AI can improve learning experiences for deaf and hard-of-hearing learners.

Accessibility for All Learn — Learning should adapt to the learner, not the other way around.
