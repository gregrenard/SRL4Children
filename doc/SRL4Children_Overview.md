# SRL4Children Beta 1.0 – Overview

## Mission and Context
SRL4Children (Safety Readiness Level for Children) is a benchmarking initiative that evaluates how conversational AI systems behave as companions for young users. Our goal is to provide policymakers, caregivers, and model builders with transparent, repeatable evidence about whether leading models are safe, supportive, and developmentally appropriate. The programme targets the top ~50 market models in free-form chitchat and personal-companion settings, covering the full 6–25 age span (Children 6–9, Tweens 9–12, Teens 13–17, Young Adults 18–25).

Progress is tracked through a two-dimensional coverage matrix: categories (Safety, Anthropomorphism, Age, Relevance, Ethics, …) intersect with age bands. Each cell highlights which criteria exist, how mature they are, and where investment is still needed. Criteria are modular by design; we extend coverage gradually to balance analytic depth with compute cost.

## Evaluation Flow
The SRL4Children interface supports an end-to-end workflow that can be replicated across model providers:

1. **Attack Benchmarks** – We stress-test a model with curated prompt suites aligned with specific risk categories. For Safety we currently focus on sexual content, hate speech, manipulation, and violence; the newest module adds **Anthropomorphism** (detecting when an AI pretends to be human through emotions, agency, sycophancy, role-play, parasocial bonding, etc.).
2. **Criteria-Based Analysis** – Each model response is scored by prompt-specific judges that enforce 0–5 scales. Analysts can review aggregate dashboards and drill into individual records to inspect prompts, responses, radar charts for subcategories, metadata, and all criterion-level explanations/evidence.
3. **Guardrail Generation (Work in Progress)** – Based on failures, the interface will surface draft guardrail instructions that product teams can plug into moderation layers or system prompts.
4. **Prompt Optimisation (Work in Progress)** – We plan to iterate model-facing prompts to raise safety scores without sacrificing utility, giving partners concrete levers to improve deployments.
5. **Synthetic Data Curation (Planned)** – High-quality failure cases can be converted into synthetic training examples for future model fine-tuning.

## Interface Highlights
- **Benchmark Explorer** – Load any benchmark folder, filter records, and export CSV summaries. The right-hand sidebar summarises the selected model’s global score, subcategory radar, and anthropomorphism snapshot when available.
- **Record Details Modal** – Tabs expose the full prompt, model answer, criterion breakdown, and (roadmap) guardrails/prompt optimisation recommendations.
- **Anthropomorphism Dashboard** – A new top-right synthesis card surfaces average scores, subcategory distributions, and radar charts to monitor human-like behaviour risks at a glance.

## Category Coverage (Current Focus)
- **Safety**: Sexual content, violence, manipulation, hate.
- **Anthropomorphism**: Emotions, agency claims, language mirroring, sycophancy, role-playing, persona projection, exclusivity claims, humor boundaries.
- **Additional domains** (Age appropriateness, Relevance, Ethics) are maintained for broader context and will continue to expand.

## Partnership Value
- **Transparent Benchmarks** – Partners can benchmark their models under identical conditions, compare against anonymised peers, and receive structured scorecards.
- **Actionable Insights** – Criterion-level evidence pinpoints failure modes, helping teams prioritise guardrails, policy updates, or fine-tuning data.
- **Collaborative Roadmap** – We invite partners to co-design new criteria (e.g., empathy, mental health), validate anthropomorphism prompts, and contribute real-world scenarios that matter for their user base.
- **Scalable Review** – Mini and full question sets (e.g., `anthropomorphism_question_mini.csv`, `anthropomorphism_question.csv`) allow quick spot-checks or comprehensive campaigns depending on budget and urgency.

## Call to Action
We are currently seeking:
- Feedback on the anthropomorphism prompts and question banks.
- Model evaluations across safety and anthropomorphism categories.
- Collaboration on the guardrail/prompt optimisation features.
- Opportunities to create synthetic datasets aligned with partner safety policies.