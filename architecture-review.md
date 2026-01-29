

***

# Minute — Architecture Review & Production Readiness Assessment

**Version:** 1.1 (Revised post-technical review)
**Date:** 29 January 2026
**Author:** Robert Fox, AI Engineer
**Classification:** Official-Sensitive

## 1. Executive Summary

The current Minute MVP architecture is built on solid, well-established asynchronous patterns derived from the i.ai Discovery template. This provides a stable foundation for the immediate ingestion, processing, and summarisation workflows required for the Pilot phase.

To mature this architecture for a Production rollout across Local Government, we must address non-functional requirements around **Security**, **Observability**, and **Cost Governance**.

This review concludes that while a major re-platforming (to a single-cloud architecture) offers long-term benefits, the immediate focus should be on **evolution and hardening** of the current stack. Major architectural migrations (e.g., to AWS Batch) are deferred to "Phase 2," contingent on usage data and cost modeling.

---

## 2. Component Review: Operational Status

*This section reviews the current stack against Production readiness criteria.*

| Component | Status | Recommendation & Rationale |
| :--- | :--- | :--- |
| **Ingestion** (S3 Pre-signed URLs) | **KEEP** | **Production Ready.** Best practice pattern for offloading bandwidth of large audio files. Highly scalable. |
| **Async Workflow** (SQS → ECS) | **KEEP** | **Retain for MVP.** Current ECS worker setup is sufficient for interactive use. **Future State:** Evaluate migration to AWS Batch or Lambda only if scaling costs become prohibitive or "scale-to-zero" becomes a hard requirement. |
| **Networking** (Private Subnets) | **KEEP** | **Production Ready.** Correct security posture. Database and Workers are isolated from the public internet. |
| **Authentication** | **UPDATE** | **Implement/ensure GDS Internal Access.** We need to integrate directly with MHCLG Entra ID (Azure AD) via OIDC to align with departmental SSO standards, and also to enforce role-based access. |
| **Speech-to-Text** (Azure Speech) | **EVALUATE** | **Retain for Rollout.** Azure provides strong diarisation. **Action:** Run a concurrent evaluation of self-hosted **WhisperX** to benchmark cost/performance for potential future migration. |
| **LLM / Summarisation** (Google Vertex) | **REVIEW** | **Dependent on APIM.** We must validate that the specific models are available via the MHCLG APIM Gateway. If not, evaluate AWS Bedrock alternatives. |
| **Database** (Aurora Postgres) | **REVIEW** | **Right-size.** Engage AWS TAM for load modeling to decide between Aurora Serverless v2 (for variable load) or standard RDS (for predictable baselines). |

---

## 3. Gap Analysis: Production Readiness

While the core logic works, the following controls are required to meet **Official-Sensitive** standards and ensure operational resilience.

### A. Security & Compliance
*   **KMS Customer Managed Keys (CMK):**
    *   *Gap:* Potential reliance on default AWS encryption.
    *   *Action:* Validate if i.AI already implemented CMKs. If not, implement them to ensure we have a cryptographic "kill switch" and granular audit trails for data decryption.
*   **Supply Chain Security:**
    *   *Action:* Enable **Amazon Inspector** on ECR to scan Docker images for CVEs (vulnerabilities) in the Python supply chain.


 *   **Static Type Checking (Mypy):**
     *   **Gap:** Python’s dynamic nature introduces risk of runtime errors as the codebase grows in complexity. 
     *  **Action:** Enforce strict **Static Typing (Mypy)** across the backend. This "hardens" the code, prevents type-related bugs before deployment, and serves as self-documentation for future developers.
     *   *Status:* Implementation currently in progress.


### B. Observability (The "Business View")
*   **Business Logic Alarms:**
    *   *Gap:* We monitor servers (CPU/RAM), but not outcomes.
    *   *Action:* Implement CloudWatch/X-Ray metrics for:
        *   `Transcription_Failure_Rate`
        *   `Job_Queue_Wait_Time` (User Experience metric)
*   **Distributed Tracing:**
    *   *Action:* Instrument the Python worker with **AWS X-Ray** to trace latency across the multi-cloud hops (AWS -> Azure -> Google).

### C. Data Governance
*   **Data Minimisation:**
    *   *Action:* Implement S3 Lifecycle Policies. Raw audio should be hard-deleted immediately after successful transcription verification (unless a user "Re-transcribe" feature is required).
*   **PII Strategy:**
    *   *Decision:* **Do Not Redact.** PII is business-critical context for Social Work summaries. Security relies on the **APIM Gateway** and **GDS Auth** rather than redaction.

---

## 4. Strategic Roadmap (Phasing)

**Phase 1: Hardening (Immediate)**
*   Integrate GDS Internal Access for Authentication.
*   Implement Business Metrics & X-Ray Tracing.


**Phase 2: Evaluation**
*   Run side-by-side benchmarks of **Azure Speech vs. WhisperX**.
*   Monitor Data Egress costs (AWS to Azure/Google).

**Phase 3: Evolution (Post-Pilot)**
*   *If costs scale linearly:* Trigger migration to **AWS Batch / Spot Instances**.
*   *If latency is high:* Trigger migration to **AWS Bedrock** to consolidate cloud footprint.



---

## 5. Next Steps / Ticket Actions

1.  **Auth:** Liaise with DevOps on GDS Internal Access integration.
2.  **Evals:** LLM-as-judge evaluation of test sample outputs.
3.  **Security:** Audit current KMS Key configuration.
4.  **Database:** Review Aurora provisioning strategy with AWS TAM.

***

