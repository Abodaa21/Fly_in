class A:
    def __init__(self):
        self.x = 1
        self.y = 2

a = A()

# __dir__ already exists (inherited from object), you can call it directly:
# print(a.__dir__())   # list of attribute names (same idea as dir(a))
# print(dir(a))        # uses a.__dir__() under the hood
x = 5
print(x.__dir__())
print(dir())