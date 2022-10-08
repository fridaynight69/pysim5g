import numpy as np

sinr = 5.9

se = np.log2(1 + 10**(sinr/10))

print(se)