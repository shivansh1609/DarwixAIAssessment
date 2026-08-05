# Q2 — Knowledge Base Retrieval Test Results

## Test Configuration

- **Embedding Model:** all-MiniLM-L6-v2 (384-dimensional embeddings, local inference)
- **Vector Database:** ChromaDB using cosine similarity
- **Retrieval Strategy:** Top-3 nearest results
- **Minimum Relevance Threshold:** 0.5

---

# Test Case 1 — Job Requirements

**User Query:**  
*"What are the requirements for the Senior Software Engineer position?"*

**Category:** Jobs

**Expected Outcome:**  
Retrieve the Senior Software Engineer job description along with the required qualifications.

**Retrieved Record:** `kb_jobs_*_c00`

**Source:**  
https://voxintel.example.com/jobs/senior-software-engineer

**Retrieved Content:**  
*"Senior Software Engineer... 5–10 years of experience... proficiency in Python, Go, or Java... experience with AWS/GCP/Azure... Docker and Kubernetes..."*

**Relevance Assessment:**  
The retrieved document directly matches the user's request by providing the required qualifications and technical skills for the role.

**Result:** ✅ Correct

---

# Test Case 2 — Qualification Rules

**User Query:**  
*"Am I eligible for a senior role if I only have three years of experience?"*

**Category:** Qualification Rules

**Expected Outcome:**  
Retrieve the qualification guidelines describing candidate eligibility.

**Retrieved Record:** `kb_qualification_*`

**Source:**  
https://voxintel.example.com/qualification-rules

**Retrieved Content:**  
*"Warm Lead (Score: 50–79)... Experience slightly outside the preferred range (±1 year)... Cold Lead (Score: 0–49)... Experience more than two years below the requirement..."*

**Relevance Assessment:**  
The retrieved policy clearly explains how candidates are evaluated. Since the requested role requires 5–10 years of experience, a candidate with only three years falls under the Cold Lead category.

**Result:** ✅ Correct

---

# Test Case 3 — Frequently Asked Questions

**User Query:**  
*"Is there any application fee?"*

**Category:** FAQ

**Expected Outcome:**  
Retrieve the FAQ confirming that candidates are not charged any application fee.

**Retrieved Record:** `kb_faq_*`

**Source:**  
https://voxintel.example.com/faq

**Retrieved Content:**  
*"TalentBridge does not charge candidates any application or recruitment fee. All hiring services are provided free of cost."*

**Relevance Assessment:**  
The retrieved FAQ provides a direct and complete answer to the user's question.

**Result:** ✅ Correct

---

# Test Case 4 — Objection Handling

**User Query:**  
*"The offered salary seems lower than my other opportunities."*

**Category:** Objection Handling

**Expected Outcome:**  
Retrieve the salary objection handling strategy.

**Retrieved Record:** `kb_objections_*`

**Source:**  
https://voxintel.example.com/objection-handling-internal

**Retrieved Content:**  
*"Acknowledge the candidate's concern. Explain the complete compensation package including bonuses, ESOPs, learning budget, and long-term growth opportunities."*

**Relevance Assessment:**  
The retrieved content specifically addresses salary-related objections and provides an appropriate response strategy.

**Result:** ✅ Correct

---

# Test Case 5 — Employee Benefits

**User Query:**  
*"What health insurance benefits are included?"*

**Category:** Benefits

**Expected Outcome:**  
Retrieve employee health insurance information.

**Retrieved Record:** `kb_benefits_*`

**Source:**  
https://voxintel.example.com/benefits-details

**Retrieved Content:**  
*"Comprehensive health insurance with ₹10,00,000 coverage for employees, spouses, and up to two dependent children. Dental and vision benefits are also included."*

**Relevance Assessment:**  
The retrieved information directly answers the query by providing complete coverage details.

**Result:** ✅ Correct

---

# Test Case 6 — Recruitment Process

**User Query:**  
*"How long does the hiring process usually take?"*

**Category:** Recruitment Process

**Expected Outcome:**  
Retrieve the interview timeline.

**Retrieved Record:** `kb_process_*`

**Source:**  
https://voxintel.example.com/screening-process

**Retrieved Content:**  
*"The complete recruitment process generally takes 2–3 weeks. Initial voice screening lasts approximately 15–20 minutes, followed by technical and final interview rounds."*

**Relevance Assessment:**  
The retrieved document directly provides the requested timeline and process overview.

**Result:** ✅ Correct

---

# Test Case 7 — Company Technology Stack

**User Query:**  
*"What technologies does the company use?"*

**Category:** Company Information

**Expected Outcome:**  
Retrieve the engineering technology stack.

**Retrieved Record:** `kb_company_*`

**Source:**  
https://voxintel.example.com/tech-stack

**Retrieved Content:**  
*"Backend: Python 3.12, Go 1.22. Frameworks: FastAPI, Gin. Databases: PostgreSQL 16, Redis 7. Frontend: React 18 with TypeScript."*

**Relevance Assessment:**  
The retrieved document accurately lists the company's technology stack, fully satisfying the user's request.

**Result:** ✅ Correct

---

# Retrieval Test Summary

| Test Case | Category | Outcome | Source Verification |
|-----------|----------|---------|---------------------|
| 1 | Job Requirements | ✅ Correct | Job Listing |
| 2 | Qualification Rules | ✅ Correct | Qualification Policy |
| 3 | Frequently Asked Questions | ✅ Correct | FAQ Documentation |
| 4 | Objection Handling | ✅ Correct | Internal Response Guide |
| 5 | Employee Benefits | ✅ Correct | Benefits Documentation |
| 6 | Recruitment Process | ✅ Correct | Hiring Process Guide |
| 7 | Company Information | ✅ Correct | Engineering Tech Stack |

---

## Overall Evaluation

- **Total Queries Tested:** 7
- **Successful Retrievals:** 7
- **Accuracy:** **100%**
- **Source Traceability:** All retrieved responses include their corresponding source reference, ensuring transparency, reliability, and verifiable knowledge retrieval.