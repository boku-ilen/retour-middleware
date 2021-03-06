import numpy as np


# returns true if string matches one of the predefined values
# case insensitive
def str_to_bool(s):
    return s.lower() in ['true', '1', 't', 'y', 'yes', 'j', 'ja']


# cuts off the third coordinate and turns into numpy array
def cut_vector(v):
    return np.array([v[0], v[1]])


# returns the length of a given vector
def length(v):
    return np.linalg.norm(v)


def get_squared_distance(point1, point2):
    """Returns the distance between two points squared (for efficiency)"""
    return (point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2
