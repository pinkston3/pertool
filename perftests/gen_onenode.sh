#!/bin/sh

PERTOOL="python -m pertool"

TEMPLATE_DIR=onenode

# Generate the directories for the CPU-only builds (no "cdyn_impl" parameter)
$PERTOOL generate -f $TEMPLATE_DIR -t "$TEMPLATE_DIR_{pertbin}" \
	--foreach "pertbin=[perturbo-nv23.1-master-atomic,perturbo-nv23.1-cptr-atomic,perturbo-nv23.1-cptr-arred]"

# Generate the directories for the CPU/GPU builds (use "cdyn_impl" parameter)
$PERTOOL generate -f $TEMPLATE_DIR -t "$TEMPLATE_DIR_{pertbin}_{cdyn_impl}" \
	--foreach "pertbin=[perturbo-nv23.1-hct-fwd-arred,perturbo-nv23.1-hct-rev-arred]" \
	--foreach "cdyn_impl=[std,tgt]"

