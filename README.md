# hako

_hako_(箱) is a library to perform manipulation and checkings on Python data collections, with high efficiency and extensibility.

## Recipes

In the following snippets, we presume `import hako as hk`.

---

**Hierarchical Checking** Instead of writing

```python
assert isinstance(vals, tuple)
for val in vals:
    assert isinstance(val, dict)
    assert 'foo' in dict and 'bar' in dict
```

_hako_ prefers

```python
assert hk.isa([hk.Tuple, hk.Dict['foo', 'bar']])(vals)
```

---

**Transposing** Instead of writing

```python
feats_1, feats_2, feats_3 = [], [], []
for batch in data:
    feat_1, feat_2, feat_3 = model(batch)
    feats_1.append(feat_1)
    feats_2.append(feat_2)
    feats_3.append(feat_3)
```

_hako_ prefers

```python
feats = [model(batch) for batch in data]
feats_1, feats_2, feats_3 = hk.transform(depth=2, perm='ab -> ba')(feats)
```

---

**Value Lifting** Instead of writing

```python
if not isinstance(x, tuple):
    x = (x,)
```

_hako_ prefers

```python
x = hk.lift(tuple)(x)
```

---

**Flattening** Instead of writing

```python
ret = []
for x in val:
    for y in x.values():
        for z in y:
            ret.append(z)
```

_hako_ prefer

```python
ret = hk.flatten(depth=3, lazy=False)(val)
```

(TODO)