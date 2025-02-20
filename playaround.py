import numpy as np

x = np.random.rand(2,2)

def softmax(x):
  return (np.exp(x).T / np.sum(np.exp(x), axis=-1)).T

print(np.sum(np.exp(x),axis = 1))
print(softmax(x))

print(x.shape[-1])