# Decision agent card

The decision agent is rule-based. It receives validated perception and mission context, applies safety
precedence, selects one allowed high-level action, and then asks the local retrieval layer to explain
that already-selected action. The explanation layer cannot override rules.

Priority order: low battery, unstable/lost communication, poor visibility, low confidence/unknown,
high anomaly, confident normal. Raw motor commands, thruster values, servo angles, battery overrides,
and instructions to ignore an operator are outside the output schema.
