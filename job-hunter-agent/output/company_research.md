# Company Overview
- **Founded:** 2004 (Adriaan Mol)  
- **Headquarters:** Amsterdam, Netherlands  
- **Employees:** ~1,000 (multidisciplinary; ~30% engineers)  
- **Industry:** Fintech (Payment Service Provider)  
- **Core Product:**  
  - A simple, API-first payment integration supporting 10+ local and global payment methods  
  - Processed €10 billion+ in transactions in 2020; on track for €20 billion in 2021  
  - Serves 120,000+ monthly active merchants (e-commerce, SaaS, SMEs)  

# Mission and Values
**Mission:**  
“To simplify financial services so that all businesses can grow—becoming the world’s most-loved PSP.”  

**Values:**  
- *Developer-First*  
  - Deep respect for engineering craft: choice of tools (MacBooks, noise-canceling headphones, etc.), autonomy in language and framework decisions  
- *Simplicity & Transparency*  
  - Clear pricing, minimal boilerplate, intuitive API design  
- *Reliability & Scalability*  
  - “Build it once, build it right”—focus on code quality, fault tolerance, and 24/7 availability  
- *Customer & Partner Partnership*  
  - Localized support in merchants’ languages, long-term relationships, shared success  
- *Continuous Learning*  
  - Rapid iteration, open feedback loops, regular “nerd-boat” demos  

# Recent News or Changes
- **Series C Funding (Jun 2021):**  
  − Raised $800 million at a $6.5 billion valuation (led by Blackstone Growth Equity).  
  − Commits to grow headcount from ~480 to ~780 over 6–9 months.  
- **Leadership Transition:**  
  − Founder Adriaan Mol handed the CEO role to fintech veteran Shane Happach in 2020.  
- **Product Expansion:**  
  − Announced upcoming working-capital loans and business-banking accounts for SMEs.  
  − Integration with open-banking rails (PSD2) and acquisition of GoCardless (Dec 2025) to unify card, bank-debit, and instant-pay flows.  
- **Geographic Growth:**  
  − Entered DACH region aggressively; now 25% of revenue.  
  − Targeting expansion in the U.K., Asia, and Latin America.  
- **Regulatory & Corporate Changes (2023–2024):**  
  − Relocated holding structure to the U.K. to segregate regulated/non-regulated entities (for license optimization).  
  − Maintaining Dutch entity for tax efficiency.  

# Role Context and Product Involvement
As a **Senior Software Engineer**, you will:  
- Design, build, maintain and optimize **RESTful APIs** and microservices that handle **thousands of transactions per second**  
- Collaborate with cross-functional teams (Product, DevOps, Security, QA) to roll out high-impact features end to end  
- Champion system-design best practices around:  
  - **Scalability:** horizontally scalable workers (RabbitMQ, Kubernetes)  
  - **Performance:** Redis caching strategies, in-memory data grids  
  - **Reliability:** idempotent operations, circuit breakers, distributed tracing  
- Drive technical initiatives, mentor mid/junior engineers, and advocate for clean code, automated testing (unit, integration), and CI/CD pipelines (GitHub Actions, Docker)  
- Contribute to architecture discussions on event streaming (Kafka), Service-Oriented Architecture, and gradually evolving legacy PHP services to Go/Java/Python  

# Likely Interview Topics
1. **System Design & Architecture**  
   - Designing a high-throughput, low-latency payments pipeline  
   - Handling peak loads, rate limiting, back-pressure strategies  
2. **API Design & Best Practices**  
   - Versioning, authentication (OAuth2, JWT), idempotency keys  
   - Error handling and developer ergonomics  
3. **Messaging & Caching**  
   - RabbitMQ patterns (pub/sub, work queues), Redis for session or rate limiting  
   - Trade-offs: in-memory vs. distributed caches  
4. **Distributed Systems Challenges**  
   - Data consistency, eventual consistency patterns, Saga orchestration  
   - Observability: logging, metrics (Prometheus/Grafana), distributed tracing (OpenTelemetry)  
5. **Security & Compliance**  
   - PCI-DSS fundamentals, encryption at rest/in transit, key management  
   - Secure coding practices, vulnerability scanning  
6. **Cloud Infrastructure**  
   - Google Cloud Platform services (Compute Engine, GKE, Pub/Sub)  
   - Infrastructure as code (Terraform)  
7. **Coding Exercise**  
   - Live or take-home test involving algorithmic logic or API implementation (PHP/Go/Java/Python)  
8. **Behavioral & Culture Fit**  
   - Collaboration stories, conflict resolution, times you led a technical initiative  

# Suggested Questions to Ask
- **Team & Tech Strategy**  
  - “Can you walk me through the current backend team structure and its roadmap for the next 6–12 months?”  
  - “What factors drive the choice between PHP, Go, Java, or Python for new services?”  
- **Scale & Reliability**  
  - “How do you measure and maintain SLAs and SLOs for your payment endpoints?”  
  - “What incident-response process and on-call rotations are in place?”  
- **Architecture Evolution**  
  - “Are there plans to refactor or replace monolithic services? How do you prioritize tech-debt vs. new features?”  
  - “What’s your vision for event streaming (Kafka) adoption across teams?”  
- **Developer Experience**  
  - “How does Mollie support engineers in choosing tools and developing new skills?”  
  - “Can you describe your code-review and CI/CD workflow?”  
- **Career Growth & Impact**  
  - “What does success look like in this role after 6 and 12 months?”  
  - “How are mentors and leadership supporting professional development here?”  
- **Product & Market**  
  - “What new payment methods or financial-services features are planned for release soon?”  
  - “How is the integration with GoCardless going to change the developer and merchant experience?”  

Good luck—go build scalable, developer-friendly payment systems that power tens of thousands of merchants every day!