# Decision agent card

The decision agent is rule-based. It receives validated perception and mission context, applies safety
precedence, selects one allowed high-level action, and then asks the local retrieval layer to explain
that already-selected action. The explanation layer cannot override rules.

Priority order: low battery, unstable/lost communication, poor visibility/turbidity, low confidence or
unknown, then domain-specific condition rules. Structural weak points lead to closer inspection; coral
stress to more imagery; debris to marking; oil-like sheen to an alert; fish activity to marking; net/cage
concerns to closer inspection. Raw actuator outputs and confirmed real-world declarations are forbidden.
