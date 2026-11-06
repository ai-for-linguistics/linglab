"""Vocabulary and theory API.

A Theory is built from an ordered list of Principles. Each Principle is a function
`apply(builder)` that may register connectives, add model constraints, or override
vocabulary primitives. Later principles override earlier ones. Principles know nothing
about theories or families: a bad combination breaks or underperforms, it is not refused.

The project (python/principles.py) supplies principles, its base models (`@base_models`)
and optional system properties (`@property_check`).

Shared syntax v2 (docs/INTERFACE.md section 1): atoms "p"; predicate application ["Student","?x"]
(a registered predicate, then terms: constants, and variables written "?x"); connectives not, and, or,
if, iff; binders ["some","?x",R,S], ["every",...], ["no",...], ["exists","?x",A], ["forall","?x",A]
(and any binder a theory registers, such as "most"); modals ["must",A], ["may",A]; any other head is a
theory-defined operator. A formula (after `translate`) is a nested tuple: an atom is a string, an operator
or connective is (head, *args), a binder is (head, "?x", *subformulas), a predicate application is
("@", name, *terms).
"""

_PRINCIPLES = {}      # id -> Principle
_PROPERTIES = {}      # name -> fn(theory) -> bool
_BASE_MODELS = []     # [fn() -> iterable of dict atom->value]
_SCOPE = ["complete"]  # what the base models cover: "complete", or how they are bounded


class Principle:
    def __init__(self, pid, apply):
        self.id, self.apply = pid, apply


def principle(pid):
    """Decorator: register `apply(builder)` as principle `pid`."""
    def deco(fn):
        _PRINCIPLES[pid] = Principle(pid, fn)
        return fn
    return deco


def base_models(fn=None, *, scope="complete"):
    """Decorator: the project's generator of candidate valuations (dicts atom -> value).
    `scope` says what the list covers: "complete" when it contains every model the theories admit (as in a
    propositional fragment), otherwise how it is bounded, for example @base_models(scope="domain size <= 3").
    A verdict that depends on having seen every model is then reported as "exhaustive within <scope>"."""
    def deco(f):
        _BASE_MODELS[:] = [f]
        _SCOPE[0] = scope or "complete"
        return f
    return deco(fn) if fn is not None else deco


def base_scope():
    return _SCOPE[0]


def bound_text(scope, base="exhaustive"):
    """"exhaustive" for a complete model list, else "exhaustive within <scope>" (same for "first n models")."""
    return base if scope in ("", "complete") else "%s within %s" % (base, scope)


def uses_quantifiers(s):
    """True if a shared-syntax sentence (or a list or dict of them) has a binder or a predicate application:
    its truth depends on a domain, which a finite model list usually bounds."""
    if isinstance(s, dict):
        return any(uses_quantifiers(v) for v in s.values())
    if not isinstance(s, list) or not s:
        return False
    if isinstance(s[0], str):
        if s[0] in RESERVED_BINDERS or (s[0] not in RESERVED_ARITY and all(isinstance(a, str) for a in s[1:]) and len(s) > 1):
            return True
        return any(uses_quantifiers(a) for a in s[1:])
    return any(uses_quantifiers(a) for a in s)


def property_check(name):
    """Decorator: register a system property `fn(theory) -> bool` for facts of type `property`."""
    def deco(fn):
        _PROPERTIES[name] = fn
        return fn
    return deco


def registered_principles():
    return _PRINCIPLES


def registered_properties():
    return _PROPERTIES


def is_var(x):
    """Variables are strings starting with '?'; constants are the other strings."""
    return isinstance(x, str) and x.startswith("?")


# Heads of the shared syntax with a fixed number of arguments (a theory may leave them undefined).
RESERVED_ARITY = {"not": 1, "and": 2, "or": 2, "if": 2, "iff": 2, "must": 1, "may": 1}
# Reserved binders: number of subformulas after the variable.
RESERVED_BINDERS = {"some": 2, "every": 2, "no": 2, "exists": 1, "forall": 1}


class Model:
    """A valuation plus a per-model cache of subformula values (the memoization).
    Propositional atoms are the scalar entries of `vals`. A model may also hold a domain and relations
    under keys the project agrees on (for example vals['domain'] = (0, 1, 2), vals['P'] = frozenset({0, 1}));
    non-scalar entries (tuple, list, set, dict) are never atoms. Quantifier operators read them."""
    def __init__(self, vals):
        self.vals = dict(vals)
        self.cache = {}
        self.size = sum(1 for v in self.vals.values() if v == 1)

    def __repr__(self):
        return "{" + ", ".join("%s=%s" % (k, v) for k, v in self.vals.items()) + "}"


class Builder:
    def __init__(self):
        self.connectives, self.constraints, self.prims = {}, [], {}
        self.operators, self.arity = {}, {}
        self.predicates, self.pred_arity, self.binders = {}, {}, {}
        self.data = {}      # free space for principles to share data (for example, alternatives)

    def connective(self, op, fn):
        """fn(*values) -> value: the operator sees only the values of its arguments at one model."""
        self.connectives[op] = fn

    def operator(self, op, fn, arity=None, binder=False):
        """fn(T, m, *subformulas) -> value: the operator sees the subformulas themselves, and may evaluate
        them at other models with T.value(m2, sub) over T.worlds() (modals, exhaustification, alternatives).
        Binder operators (binder=True; "some", "every", "no", "exists", "forall" always are) are called as
        fn(T, m, x, *subformulas) with the bound variable name x (for example "?x"); they evaluate the body
        under an assignment with T.value(m, body, T.bind(x, d)). `arity` counts the subformulas (not x).
        Inside any operator, T.value(m2, sub) keeps the current assignment of variables."""
        self.operators[op] = fn
        if binder or op in RESERVED_BINDERS:
            self.binders[op] = arity if arity is not None else RESERVED_BINDERS.get(op, 2)
        elif arity is not None:
            self.arity[op] = arity

    def predicate(self, name, fn, arity=None):
        """fn(T, m, *term_values) -> value: the value of the predicate applied to individuals (variables
        already replaced by their assignment, constants passed as written)."""
        self.predicates[name] = fn
        if arity is not None:
            self.pred_arity[name] = arity

    def constrain(self, fn):
        self.constraints.append(fn)

    def set(self, name, fn):
        self.prims[name] = fn


# Defaults of the vocabulary primitives (a principle may override any of them).
def _ent_ok(T, m, prem, concl):
    return not all(T.true_in(m, p) for p in prem) or T.true_in(m, concl)


def _felic_ok(T, m, disc):
    return all(T.defined_in(m, f) for f in disc)


def _cons_ok(T, m, prem):
    return all(T.true_in(m, p) for p in prem)


class Theory:
    OPS = RESERVED_ARITY

    def __init__(self, tid, name, principle_ids, registry=None):
        self.id, self.name, self.principle_ids = tid, name, list(principle_ids)
        registry = _PRINCIPLES if registry is None else registry
        b = Builder()
        for pid in self.principle_ids:
            if pid not in registry:
                raise KeyError("principle %s has no Python code" % pid)
            registry[pid].apply(b)
        self.connectives, self.constraints = b.connectives, b.constraints
        self.operators, self.data = b.operators, b.data
        self.predicates, self.pred_arity, self.binders = b.predicates, b.pred_arity, b.binders
        self.ops = dict(self.OPS)
        self.ops.update(b.arity)
        self._env = {}      # ambient assignment of variables (see value / bind)
        self._fv = {}       # formula -> its free variables
        p = b.prims
        self._true_in, self._defined_in = p.get("true_in"), p.get("defined_in")
        self._describe = p.get("describe_model")     # optional hook: model -> readable text
        self._ms = None
        self._ent, self._felic, self._cons = (p.get("ent_ok", _ent_ok),
                                              p.get("felic_ok", _felic_ok),
                                              p.get("cons_ok", _cons_ok))
        # "forall" (default): felicitous iff the discourse is felicitous in every model.
        # A principle may set "felic_kind" to "exists" (felicitous in some model).
        self.felic_kind = p.get("felic_kind", "forall")
        self._atoms = None

    # -- models -------------------------------------------------------------
    def atoms(self):
        if self._atoms is None:
            first = next(iter(_BASE_MODELS[0]()), {}) if _BASE_MODELS else {}
            self._atoms = {k for k, v in first.items() if not isinstance(v, (tuple, list, set, frozenset, dict))}
        return self._atoms

    def models(self, bound=None):
        """Models satisfying the theory's constraints, smallest first, deterministic.
        `bound` caps the number of models yielded (the size bound)."""
        n = 0
        for m in self.worlds():
            if bound is not None and n >= bound:
                return
            n += 1
            yield m

    def worlds(self):
        """All admissible models, as one shared list (so cached values are shared). Operators that quantify
        over other models (modals, exhaustification) iterate over this."""
        if self._ms is None:
            if not _BASE_MODELS:
                raise RuntimeError("the project defines no @base_models")
            ms = sorted((Model(v) for v in _BASE_MODELS[0]()), key=lambda m: m.size)  # stable
            self._ms = [m for m in ms if all(c(m) for c in self.constraints)]
        return self._ms

    def describe(self, m):
        return self._describe(self, m) if self._describe else repr(m)

    # -- syntax -> formulas -------------------------------------------------
    def _is_binder(self, h):
        return h in self.binders and h in self.operators

    def _tr(self, s, bound):
        """-> (formula, '') or (None, reason). The one code path of `translate` and `explain`."""
        if isinstance(s, str):
            if is_var(s):
                return None, "variable %r used as a sentence" % s
            return (s, "") if s in self.atoms() else (None, "unknown atom %r" % s)
        if not isinstance(s, (list, tuple)) or not s or not isinstance(s[0], str):
            return None, "malformed sentence %r" % (s,)
        h, args = s[0], list(s[1:])
        if self._is_binder(h):
            if len(args) != 1 + self.binders[h]:
                return None, "operator %r takes a variable and %d formula(s)" % (h, self.binders[h])
            x = args[0]
            if not is_var(x):
                return None, "operator %r needs a variable (like '?x') as first argument, got %r" % (h, x)
            subs = []
            for a in args[1:]:
                f, why = self._tr(a, bound | {x})
                if f is None:
                    return None, why
                subs.append(f)
            return (h, x) + tuple(subs), ""
        if h in self.connectives or h in self.operators:
            if len(args) != self.ops.get(h, len(args)):
                return None, "operator %r takes %d argument(s)" % (h, self.ops[h])
            subs = []
            for a in args:
                f, why = self._tr(a, bound)
                if f is None:
                    return None, why
                subs.append(f)
            return (h,) + tuple(subs), ""
        if h in self.predicates:
            if not args or len(args) != self.pred_arity.get(h, len(args)):
                return None, "predicate %r takes %s term(s)" % (h, self.pred_arity.get(h, "at least one"))
            for a in args:
                if not isinstance(a, str):
                    return None, "predicate %r applies to terms (constants or '?x' variables), got %r" % (h, a)
                if is_var(a) and a not in bound:
                    return None, "variable %r is not bound" % a
            return ("@", h) + tuple(args), ""
        kind = "predicate or operator" if args and all(isinstance(a, str) for a in args) else "operator"
        return None, "%s %r not defined by any principle of this theory" % (kind, h)

    def translate(self, s):
        """Shared syntax -> formula (nested tuples), or None if not expressible (unknown atom, predicate or
        operator, wrong arity, unbound variable)."""
        return self._tr(s, frozenset())[0]

    def explain(self, s):
        """A short reason why `translate(s)` is None (the first untranslatable part), or '' if it translates."""
        return self._tr(s, frozenset())[1]

    # -- semantics ----------------------------------------------------------
    def free_vars(self, f):
        r = self._fv.get(f)
        if r is None:
            if isinstance(f, str):
                r = frozenset()
            elif f[0] == "@":
                r = frozenset(x for x in f[2:] if is_var(x))
            elif self._is_binder(f[0]):
                r = frozenset().union(*(self.free_vars(a) for a in f[2:])) - {f[1]}
            else:
                r = frozenset().union(*(self.free_vars(a) for a in f[1:]))
            self._fv[f] = r
        return r

    def bind(self, x, d):
        """The current assignment extended with x -> d (to evaluate the body of a binder)."""
        return dict(self._env, **{x: d})

    def value(self, m, f, env=None):
        """Value of formula f at model m under assignment env (default: the current one, {} at top level).
        Memoized per model, keyed by the formula and the values of its free variables only."""
        if env is None:
            env = self._env
        if isinstance(f, str):
            return m.vals[f]
        fv = self.free_vars(f)
        key = f if not fv else (f, tuple(sorted((x, env[x]) for x in fv)))
        if key in m.cache:
            return m.cache[key]
        old, self._env = self._env, env
        try:
            if f[0] == "@":
                v = self.predicates[f[1]](self, m, *[env[x] if is_var(x) else x for x in f[2:]])
            elif f[0] in self.operators:
                v = self.operators[f[0]](self, m, *f[1:])
            else:
                v = self.connectives[f[0]](*[self.value(m, a, env) for a in f[1:]])
        finally:
            self._env = old
        m.cache[key] = v
        return v

    def true_in(self, m, f):
        if self._true_in:
            return self._true_in(self, m, f)
        return self.value(m, f) == 1

    def defined_in(self, m, f):
        if self._defined_in:
            return self._defined_in(self, m, f)
        return self.value(m, f) != "#"

    def ent_ok(self, m, prem, concl):
        return self._ent(self, m, prem, concl)

    def felic_ok(self, m, disc):
        return self._felic(self, m, disc)

    def cons_ok(self, m, prem):
        return self._cons(self, m, prem)
