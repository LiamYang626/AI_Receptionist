ans = 0
n = 1
num = 1
count = 0
prime = 0
while n <= 199:
    add = n*n
    if n%3 == 0:
        add = -add
    ans += add
    n += 1

while num <= ans:
    if (ans%num == 0):
        index = 2
        while index < num:
            if (num%index == 0):
                break
            index += 1
            if index == num - 1:
                if prime != num:
                    count += 1
                prime = num
    num += 1
print(count)