"""Pure, conservative relationships between cask releases and DMG detection text."""
from dataclasses import dataclass
import re


INSPECTOR_VERSION = "dmg-inspector/1"
# PR377 is distributed at 0d32caa and its fresh live-source checks passed;
# Website 7027bfa also passed the recorded pair matrix before this producer.
CATALOG_CONSUMER_CAPABILITIES = frozenset({"decorated_text", "plus_build"})
_CORE = r"[0-9]+(?:\.[0-9]+)*"
_CANON = r"(?:0|[1-9][0-9]*)"
_BOUNDED_COMPONENT = r"(?:0|[1-9][0-9]{0,8})"
_BOUNDED_TRIPLET = _BOUNDED_COMPONENT + r"(?:\." + _BOUNDED_COMPONENT + r"){2}"
_PRERELEASE_CASK_PARTS = frozenset({"alpha", "beta", "dev", "developer", "canary", "nightly",
                                    "preview", "rc", "unstable", "insider", "insiders",
                                    "prerelease", "testing"})


@dataclass(frozen=True)
class BundleObservation:
    artifact_sha256: str
    bundle_id: str
    short_version: str
    bundle_version: str = None
    inspector: str = INSPECTOR_VERSION


@dataclass(frozen=True)
class InspectionRefusal:
    code: str
    integrity: bool
    artifact_sha256: str = None


@dataclass(frozen=True)
class PriorEntry:
    version: str = None
    sha: str = None
    url: str = None


@dataclass(frozen=True)
class ReconcileInput:
    source_release: str
    legacy_version: str
    declared_sha256: str
    url: str
    bundle_id: str
    prior: PriorEntry = None
    observation: object = None
    consumer_caps: frozenset = CATALOG_CONSUMER_CAPABILITIES
    source_cask: str = None


@dataclass(frozen=True)
class Decision:
    action: str
    version: str = None
    sha: str = None
    relation: str = None
    reason: str = ""
    verified: bool = False


def generic_legacy_truncate(raw):
    return raw.split(",")[0].split("_")[0]


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def plan(i):
    """Called only for eligible vendor DMGs; never reuses positive metadata."""
    if (i.prior and _sha(i.declared_sha256) and i.declared_sha256 == i.prior.sha
            and i.url == i.prior.url):
        return Decision("NOOP", i.prior.version, i.prior.sha, reason="SAME_PINNED_ARTIFACT")
    if i.prior and i.legacy_version == i.prior.version:
        return Decision("LEGACY", i.legacy_version, reason="UNCHANGED_LEGACY_VERSION")
    return Decision("INSPECT", reason="CHANGED_DETECTION_VERSION")


def relationship(raw, short):
    """Every accepted non-padding character is present in the raw release."""
    if not isinstance(raw, str) or not isinstance(short, str) or len(raw) > 256:
        return None
    if re.fullmatch(_CORE, raw) and re.fullmatch(_CORE, short):
        longer, shorter = sorted((raw, short), key=len, reverse=True)
        if longer.startswith(shorter) and re.fullmatch(r"(?:\.0)+", longer[len(shorter):]):
            return "PAD"
    fields = raw.split(",")
    if (len(fields) < 2 or not re.fullmatch(_CORE, fields[0])
            or not re.fullmatch(r"[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*", fields[1])
            or not all(re.fullmatch(_CANON, f) for f in fields[2:])):
        return None
    core, extra = fields[:2]
    if re.fullmatch(_CANON, extra):
        if "." in core and short == core + "+" + extra:
            return "RENDER_PLUS"
        if short == core + " (build " + extra + ")":
            return "RENDER_PAREN_BUILD"
    if re.fullmatch(r"stable(?:\." + _CANON + r")?", extra) and short == core + "-" + extra:
        return "RENDER_CHANNEL"
    return None


def build_relationship(raw, short, build):
    """Bind numeric source components to the same bundle's short and build text."""
    if (type(raw) is not str or type(short) is not str or type(build) is not str
            or len(raw) > 256 or len(short) > 64 or len(build) > 64
            or not build.isprintable()):
        return None
    numeric = _CANON + r"(?:\." + _CANON + r")*"
    if not re.fullmatch(_CANON + r"(?:\." + _CANON + r")+", short):
        return None
    if re.fullmatch(numeric, raw) and build == raw and raw.startswith(short + "."):
        return "SOURCE_BUILD_EXACT"
    fields = raw.split(",")
    if (len(fields) in {1, 2} and (len(fields) == 1 or fields[1] == short)
            and re.fullmatch(numeric, fields[0]) and re.fullmatch(_CANON, build)
            and fields[0] == short + "." + build):
        return "SOURCE_SHORT_DOT_BUILD"
    return None


def hyphen_build_relationship(raw, short, build, cask):
    """Bind a stable cask's triplet-build release to exact same-file bundle text.

    The selected stable Homebrew cask is the accepted channel authority. Numeric
    suffixes alone cannot exclude prereleases: 1.2.3-1 may pass this rule and a
    later 1.2.3 final release would refresh, rather than offer another update.
    Explicit prerelease/versioned casks do not gain that channel assumption.
    """
    if (type(raw) is not str or type(short) is not str or type(build) is not str
            or type(cask) is not str or len(raw) > 256 or len(short) > 64
            or len(build) > 64 or len(cask) > 128 or not build.isprintable()
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", cask)
            or _PRERELEASE_CASK_PARTS.intersection(cask.split("-"))):
        return None
    match = re.fullmatch(r"(" + _BOUNDED_TRIPLET + r")-([1-9][0-9]{0,17})", raw)
    if match and short == match[1] and build in {match[2], short + "." + match[2]}:
        return "SOURCE_HYPHEN_BUILD"
    return None


def parse_detection(value):
    if not isinstance(value, str) or len(value) > 256:
        return None
    match = re.fullmatch(r"(" + _CORE + r")(?:\+" + _CANON
                         + r"| \(build " + _CANON + r"\)|-stable(?:\." + _CANON + r")?)?", value)
    return tuple(int(part) for part in match[1].split(".")) if match else None


def reconcile(i):
    obs = i.observation
    if isinstance(obs, InspectionRefusal):
        if obs.integrity:
            return Decision("HOLD", reason=obs.code)
        # Existing unreadable-artifact behavior, never a newly inferred version.
        return Decision("LEGACY_PASS", i.legacy_version, obs.artifact_sha256,
                        reason=obs.code, verified=False)
    if (not isinstance(obs, BundleObservation) or obs.bundle_id != i.bundle_id
            or obs.inspector != INSPECTOR_VERSION or not _sha(obs.artifact_sha256)
            or (i.declared_sha256 is not None and i.declared_sha256 != obs.artifact_sha256)):
        return Decision("HOLD", reason="OBSERVATION_INCONSISTENT")
    if (not isinstance(i.source_release, str) or not isinstance(obs.short_version, str)
            or not 0 < len(obs.short_version) <= 64 or not obs.short_version.isprintable()):
        return Decision("HOLD", reason="RELATION_UNPROVEN")
    if i.legacy_version != generic_legacy_truncate(i.source_release):
        relation = "BRANCH_EXACT" if obs.short_version == i.legacy_version else None
    elif obs.short_version == i.legacy_version:
        relation = "EXACT"
    else:
        relation = (relationship(i.source_release, obs.short_version)
                    or build_relationship(i.source_release, obs.short_version, obs.bundle_version)
                    or hyphen_build_relationship(i.source_release, obs.short_version,
                                                 obs.bundle_version, i.source_cask))
    if relation is None:
        return Decision("HOLD", reason="RELATION_UNPROVEN")
    required = {"RENDER_PLUS": "plus_build", "RENDER_PAREN_BUILD": "decorated_text",
                "RENDER_CHANNEL": "decorated_text"}.get(relation)
    if required and required not in i.consumer_caps:
        return Decision("HOLD", relation=relation, reason="CONSUMER_CAPABILITY_PENDING")
    short, digest = obs.short_version, obs.artifact_sha256
    if i.prior:
        if short == i.prior.version:
            action = "NOOP" if digest == i.prior.sha and i.url == i.prior.url else "REFRESH"
            return Decision(action, short, digest, relation, "EXACT_TEXT_UNCHANGED", True)
        new, old = parse_detection(short), parse_detection(i.prior.version)
        if relation == "SOURCE_HYPHEN_BUILD" and old is None and type(i.prior.version) is str:
            # Compare only the release core, whose strict advance wins under
            # both prerelease and build interpretations of the old suffix.
            prior = re.fullmatch(r"(" + _BOUNDED_TRIPLET + r")-(?:0|[1-9][0-9]{0,17})",
                                 i.prior.version)
            if prior:
                old = tuple(int(part) for part in prior[1].split("."))
        if new is None or old is None:
            if relation not in {"EXACT", "BRANCH_EXACT"}:
                return Decision("HOLD", relation=relation, reason="PRIOR_ORDER_UNKNOWN")
            # Preserve today's exact-match lane for opaque legacy version formats.
        else:
            n = max(len(new), len(old))
            new, old = new + (0,) * (n - len(new)), old + (0,) * (n - len(old))
            if new <= old:
                reason = "DETECTION_REGRESSION" if new < old else "EQUAL_ORDER_TEXT_DIFFERS"
                return Decision("HOLD", relation=relation, reason=reason)
    return Decision("WRITE", short, digest, relation, "PROVEN_DETECTION_TEXT", True)
