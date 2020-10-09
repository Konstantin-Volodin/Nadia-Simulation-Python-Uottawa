import numpy as np


test = np.random.RandomState()

test.seed(1)
print(test.random())

test.seed(1)
print(np.random.random())
print(test.random())