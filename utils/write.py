import pickle


def pickle_dump(obj, name):
    file1 = open(name, 'wb')
    # dump information to that file
    pickle.dump(obj, file1)
    # close the file
    file1.close()