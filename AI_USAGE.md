# AI_USAGE.md

## How this was built

I used Claude as an AI-assisted reasoning and discussion tool during this project. The implementation, corpus sourcing, calculations, analysis, and written deliverables were my own work.

I was responsible for the project's technical decisions, implementation, calculations, conclusions, and final write-ups. AI was used primarily to understand the problem, explore approaches, identify things worth checking, and cross-check work I had already performed.

My own contribution included:

- **Implementation.** I wrote the implementation and supporting scripts myself, including the audit, corpus preparation, tokenizer training, experiments, and benchmarking code.
- **Corpus sourcing and experimental setup.** I investigated the FLORES-200 access constraint, selected an appropriate substitute corpus, and made the decisions about the data, train/evaluation split, tokenizer setup, and experimental methodology.
- **Analysis and calculations.** I performed the Part B arithmetic and capacity calculations myself. AI helped explain the concepts and approach, after which I independently calculated and cross-checked the results.
- **Part A investigation.** I examined `fertility.py`, investigated the planted bugs, and determined the findings myself. AI provided a second perspective on what to inspect and how behaviors could be verified.
- **Part C reasoning and decision-making.** I used AI to brainstorm and compare SFT, a rewriter model, and a prompt-only approach. I then used my own judgment to select and develop the final approach.
- **Written deliverables.** I drafted the four write-ups myself. AI was used as a discussion and review aid, not as the author.
- **Sequencing and scope.** I determined the order of work (A1→A4, then B, then C), what to investigate, and when there was sufficient evidence to proceed.
- **Quality control and compliance.** I used AI to review the work against the assignment requirements, while making the final corrections and decisions myself.
- **Final authority.** AI suggestions were not treated as authoritative. I evaluated them against the code, experiments, calculations, and assignment requirements before making final decisions.

## Where AI helped me

AI was most useful as a reasoning and verification aid rather than as the creator of the work.

- **Understanding the problem and choosing an approach.** AI helped clarify background concepts, discuss possible approaches, and identify useful lines of inquiry before I performed the actual work.
- **Part B conceptual guidance.** The arithmetic and capacity analysis were my own. AI helped me understand the underlying concepts, identify the relevant quantities, and discuss possible derivations. I then performed and independently checked the calculations.
- **Sanity checking calculations.** After completing my calculations, I used AI as a second pair of eyes to identify possible arithmetic or reasoning mistakes. Agreement with benchmark data provided an additional consistency check.
- **Corpus-access constraint.** AI helped me reason about the practical consequences of FLORES-200 being inaccessible and discuss defensible alternatives. I investigated and selected the substitute corpus and designed the experimental setup myself.
- **Exploring Part C alternatives.** AI helped brainstorm and compare SFT, rewriter-model, and prompt-only approaches. I evaluated those options using my own judgment and developed the final approach.
- **Review and quality control.** AI helped identify unsupported arguments, unclear assumptions, or potentially missed requirements. These reviews were advisory; I made the final decisions.
- **Second-opinion reasoning.** AI provided another perspective on technical questions, but I checked conclusions against the code, experiments, calculations, and available evidence rather than treating AI responses as evidence.

## Where AI could have misled me if I hadn't been checking

The most useful lessons came from actual mistakes and omissions during the project.

- **Part A evidence requirements.** The initial Part A work appeared more complete than it was: the required A2 write-up was missing, and the individual bug findings were not exposed through reproducible per-claim CLI commands. I caught this by explicitly checking the work against the assignment's evidence requirements. This reinforced that AI-assisted work can sound complete without satisfying every rubric requirement.
- **Toy tokenizer and Bug 2.** An early analysis suggested that `.lower()` inflated the headline fertility gap. Testing with the real GPT-2 tokenizer produced the opposite result, so I did not carry the toy-tokenizer conclusion into the final analysis. This showed that simplified experiments may not transfer to a real pretrained tokenizer.
- **Toy-tokenizer capacity results.** Results such as the approximately 6–8× difference between reported and honest goodput and the roughly 25-sequence KV-cache ceiling were valid only under the experiment's specific assumptions, including the decimal-GB convention, toy tokenizer, and training data. They should not be treated as universal model-serving characteristics.
- **Independent evidence checking.** AI could suggest or verify interpretations of benchmark data, but the arithmetic and derivations were mine. Agreement with AI was a cross-check, not proof. The benchmark log and my own derivation remained the primary evidence.

These experiences reinforced the role I intended AI to play: a useful assistant for understanding, brainstorming, questioning, and cross-checking—not the authority over the work. When AI suggestions conflicted with the actual code, experiments, calculations, or assignment requirements, I relied on the evidence and my own judgment.
