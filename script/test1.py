def funcA(A):
    print("function A")
    return A

def funcB(B):
    print("function B")
    return B

@funcA
@funcB
def func(c):
    print("function C")
    return c**2

print(globals())