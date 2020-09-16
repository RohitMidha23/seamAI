import numpy as np 

sub = np.load("submission.npz")
sub = sub["prediction"]

assert sorted(list(np.unique(sub))) == list(range(1,7)), "[ERR] labels wrong"
assert sub.shape == (1006, 782, 251) 

print("[INFO] All checks passed!")