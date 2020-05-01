

class Vector:
    """
    Maybe using this class for support of a vector ?
    """

    def __init__(self, vector: list=None, from_sentence: str=None):
        """
        Make a Vector intence either by a list corresponding to the vector, or either by a sentence,
        in wich case the sentence will be transformed to a vector.
        :param vector: list of number
        :type vector: list
        :param from_sentence: sentence wich will be transform in a vector
        :type from_sentence: str
        """
        if vector is not None:
            self.vector = vector
        elif from_sentence is not None and type(from_sentence) is str:
            self.vector = self.sentence_to_vector(from_sentence)

    # Si tu préfères ne pas utiliser la classe, il faut extraire cette fonction la de la classe
    @staticmethod
    def sentence_to_vector(sentence: str):
        """
        Transform a sentence to a vector
        :param sentence: sentence to transform into a list
        :type sentence: str
        :return: vector (formated as you will need for proximity function -> Maybe construct a class for it ?)
        """
        return None

    # Si tu préfères ne pas utiliser la classe, utiliser l'autre fonction 'get_proximity' juste en dessous
    def get_proximity(self, vector):
        """
        Get a proximity score between the self instance and the other vector instance.
        :param vector: other vector to compare distance.
        :type vector: Vector
        :return: proximity score (float)
        """
        return 0.


# Si tu ne veux pas utiliser la classe, utiliser cette fonction la pour la proximité
def get_proximity(reference: list, other: list):
    """
    Get a proximity score between the reference vector and the other vector.
    :param reference: reference vector to compare distance.
    :type reference: list
    :param other: other vector to compare distance.
    :type other: list
    :return: proximity score (float)
    """
    return 0.

