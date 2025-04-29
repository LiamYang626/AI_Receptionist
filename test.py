m = 1
n = 1
p = 9 - m - n
a = 1 
b = 1 
c = 9 - a - b
red = [m, n, p]
green = [a, b, c]

def calculate(m, n, p):
    if a == m:
        if b == n:
            if c == p:
                return True
            
    

result = False

while True:
    while True:
        n += 1
        p = 104 - m - n
        if p <= 0:
            break
        if m + n + p == 104:
            result = calculate(m, n, p)
        if result:
            print(f"m: {m}, n: {n}, p: {p}")
    m += 1
    n = 1 
    p = 104 - m - n
    if m == 103:
        break
    if m + n + p == 104:
        result = calculate(m, n, p)
    if result:
        print(f"m: {m}, n: {n}, p: {p}")
        break
print(f"m: {m}, n: {n}, p: {p}")
