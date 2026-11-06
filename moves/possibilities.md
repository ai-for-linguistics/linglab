# possibilities: ideas to have in mind and to propose when the time comes

Not features to build now. The report is a living thing: users will propose changes to content and to the page. Know these options so that you can react well to a proposal, or suggest one when the data call for it. Say what it would change before doing it, and keep the defaults light.

**Show theories by any property.** A theory has properties: its paper, its family, its kind, which principles it contains, who proposed it. Today the Theories × Facts view groups by family. Any property can be the grouping key (origin, kind, "has principle P" yes/no, none). A theory with several values (derived from two others, containing several principles) can appear in each cluster, marked as repeated. Suggest this when there are more than a dozen theories or when families do not exist.

**Readings.** A cell can carry an explanation of what happened (`data/readings.json`): how the proof seems to work, why a run fails. Never evidence, and never changes a verdict. Write one when you settle a cell; offer to write them for the cells a user opens most.

**Probes and linking hypotheses.** Facts are observations of a few probe types (judgment, inference, comparison, scenario, preference). A theory's adapter is its linking hypothesis: how its internal notions (presupposition, implicature) predict a behaviour. Useful when two theories disagree about *what the datum means*, not only about whether it holds. See `utils/docs/MODEL.md`.

**Reasons for out of scope.** Three: the sentence is outside the theory's fragment; the theory makes no prediction for this probe; a primitive is not implemented (including one the theory's source leaves to another mechanism). Offer to record the reason when many cells are out of scope.

**Text or shared spec.** A fact always keeps its text; a formal spec is optional (one per reading when ambiguous). A theory may read the spec or bring its own parser as principles about structure. Suggest it when a fact cannot be written in the shared syntax.

**Layers beyond two.** Reliability layers (uncontroversial, controversial, nice-to-have, to be clarified) are plain properties of facts; more layers need no new machinery.

**A shared index.** A plain registry of theories and facts created by users, with an id convention (`paper-key:example-id`) and the syntax version, so that others can reuse or compare them. Linglib, when it has what is needed, is a source and a place to contribute formal studies.

**Other views.** Transposed matrix (facts as rows), two theories side by side, which facts separate these theories, principle ablation (needs computing variants, not only display), a tab built from a user's question. Ask before adding a tab; the user decides what to keep.

**Prompt**
> What display or workflow options do you see for this project, given its size and its data? Propose two, say what each would change, and wait for my choice.
