def gen():
    a = 10
    yield a
    a += 5
    yield a
g = gen()

print(next(g))
print(g.gi_frame.f_locals)
