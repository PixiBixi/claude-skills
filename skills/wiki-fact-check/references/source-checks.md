# Source checks

Upstream docs lag or lie more often than expected, and precisely on the subtle points. For claims in families 1, 3 and 4 (defaults, names, behaviours), read the source, not just the doc page. When docs and code disagree, code wins and the report flags the contradiction.

## Contents

- Where the answer lives
- Checks the source makes cheap
- Cases that motivated these rules

## Where the answer lives

| Question | Where the answer lives |
|---|---|
| Default value of a flag | The flag declaration under `cmd/`, or generated help. Never a blog post |
| Exact name of a metric | Its definition (`promauto.New...`), including any prefix added by a `WrapRegistererWithPrefix` |
| A Kubernetes API field and its default | `kubernetes/api`, `core/v1/types.go`, the field comment |
| GA or beta | `pkg/features/kube_features.go` for Kubernetes, the CHANGELOG otherwise |
| A borrowed performance number | The originating PR or benchmark. An unsourced round number is almost always wrong |
| A CLI behaviour | The subcommand's code first, the docs second |
| A tool's output or error message | Run it when that is cheap and paste what it prints. Rebuilding it from the source misses what the run prints first |

## Checks the source makes cheap

- **Version.** A behaviour can be true for the version deployed and false for the reader's. Find when it changed (`git log -S` on the function, then `git tag --contains`) and flag a claim that does not date itself.
- **Our own config.** A passage describing the author's setup (layers, flags, ApplicationSet shape) is checked against the current repo, not memory. Check the version actually running too (`kubectl get pods -o jsonpath` on the image): a chart default can pin an older release than the repo suggests.
- **A fix named in a PR title.** "Fixed in vX" is verified by reading what the fix computes, not what it is called.
- **A Kubernetes recipe that runs privileged.** Ask which namespace it changes and whether a native path exists (`securityContext.sysctls`, Pod Security level).
- **A third-party bug described in the present tense.** Search upstream for a later fix (`git log --grep`, `git tag --contains`) and compare with the deployed version.

## Cases that motivated these rules

Versions below are those of the original check, kept as examples, not as facts to reuse.

- Thanos `query-frontend.md` claimed only range queries go through the frontend, while `roundtrip.go` defined a `newInstantQueryTripperware` since 0.35.
- An agent reported `thanos_bucket_store_series_gate_duration_seconds`. The real name, `..._gate_queries_duration_seconds`, was readable only in `pkg/gate/gate.go`.
- Thanos receive RF=2 needed both replicas to ack until v0.37 (PR #7669), then a quorum of 1: an undated claim was false for one side.
- Thanos `ObjectStorageConfigHash` (PR #6880) hashes the caching-bucket config plus its file path, not the object-store config, so 2 stacks sharing one backend still collided in v0.42 despite the PR title.
- A `sysctl -w` initContainer in a `hostNetwork` pod rewrites the node for every host-network process, since the kubelet rejects `net.*` sysctls there (`pkg/kubelet/sysctl/allowlist.go`). In a pod with its own netns, `securityContext.sysctls` does it unprivileged, safe or unsafe per `safe_sysctls.go`, and Pod Security `baseline` admits only the safe ones.
- Dragonfly emits its zero-valued eviction counters since v2.0.0 (PR #8052), while prod ran v1.37.
- An agent rebuilt the `renovate-config-validator` message from `validation.ts` and quoted a warning, while the run prints an error first.
